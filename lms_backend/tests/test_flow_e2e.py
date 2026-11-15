"""Flujo completo de la demo, de punta a punta por HTTP:

instructor -> curso premium con certificado -> lecciones con duración ->
evaluación publicada -> clase en vivo grabada -> estudiante -> pago ->
inscripción automática (Observer) -> contenido (Proxy) -> completar lecciones
(Visitor) -> rendir evaluación (State) -> certificado -> notificaciones ->
recomendaciones; más los casos 401/403/409. Incluye el seed de demostración.
"""

from app.main import app
from app.modules.auth.application.dtos import UserRegisterDTO
from app.modules.auth.application.use_cases import RegisterUserUseCase
from app.modules.auth.domain.models import Role
from app.shared.infrastructure import container
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository
from scripts import seed

PWD = "Secreta123"


def _login(client, email, role, first="Ana", last="Perez"):
    r = client.post("/auth/register", json={"first_name": first, "last_name": last,
                    "email": email, "password": PWD, "role": role})
    assert r.status_code in (201, 409)
    r = client.post("/auth/login", json={"email": email, "password": PWD})
    assert r.status_code == 200
    body = r.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]["user_id"]


def _admin(client):
    db = next(app.dependency_overrides[get_db]())
    RegisterUserUseCase(SqlAlchemyUserRepository(db)).execute(UserRegisterDTO(
        first_name="Ad", last_name="Min", email="admin@x.com", password=PWD, role=Role.ADMIN))
    r = client.post("/auth/login", json={"email": "admin@x.com", "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_flujo_completo_de_la_demo(client):
    # ---------------------------------------------------------- instructor
    inst, inst_id = _login(client, "prof@x.com", "instructor", "Iván", "Profe")
    r = client.post("/courses/", json={"title": "Patrones", "price": 49.9,
                    "course_type": "video", "premium": True, "certificate": True},
                    headers=inst)
    assert r.status_code == 201, r.text
    course = r.json()
    cid = course["id"]
    assert course["premium"] is True and course["instructor_id"] == inst_id
    # Otro curso del mismo instructor (para la recomendación final).
    nxt = client.post("/courses/", json={"title": "Patrones II", "price": 0,
                      "course_type": "video"}, headers=inst).json()["id"]

    lessons = []
    for module, minutes, kind in [("Comportamiento", 20, "video"),
                                  ("Comportamiento", 25, "video"),
                                  ("Estructurales", 15, "quiz")]:
        r = client.post(f"/courses/{cid}/content/lessons", json={
            "module_title": module, "title": f"L{len(lessons)}", "media_id": "m",
            "provider": "vimeo", "lesson_type": kind, "duration_minutes": minutes},
            headers=inst)
        assert r.status_code == 201
        lessons.append(r.json()["lesson_id"])

    aid = client.post("/assessments", json={"course_id": cid, "title": "Parcial",
                      "passing_score": 60, "max_attempts": 2}, headers=inst).json()["id"]
    qids = [client.post(f"/assessments/{aid}/questions", json={
        "text": f"P{i}", "options": ["a", "b", "c"], "correct_option": 2, "points": 5},
        headers=inst).json()["question_id"] for i in range(2)]
    assert client.post(f"/assessments/{aid}/publish", headers=inst).json()["state"] == "published"

    sid = client.post("/live-sessions", json={"course_id": cid, "title": "Clase 1"},
                      headers=inst).json()["id"]
    client.post(f"/live-sessions/{sid}/start", headers=inst)
    recorded = client.post(f"/live-sessions/{sid}/end", headers=inst).json()
    assert recorded["state"] == "recorded" and recorded["recording_url"]

    # ---------------------------------------------------------- estudiante
    alum, alum_id = _login(client, "sofia@x.com", "student", "Sofía", "Ruiz")

    # Sin pago: 403 en inscripción, contenido, progreso y evaluación.
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 403
    assert client.get(f"/courses/{cid}/content", headers=alum).status_code == 403
    assert client.get(f"/courses/{cid}/progress/me", headers=alum).status_code == 403
    assert client.post(f"/courses/{cid}/lessons/{lessons[0]}/complete",
                       headers=alum).status_code == 403
    r = client.post(f"/assessments/{aid}/attempts", json={"answers": {}}, headers=alum)
    assert r.status_code == 403
    # Estudiante nuevo: se le sugiere el curso gratuito para empezar.
    recs = client.get("/recommendations/me", headers=alum).json()
    assert [(x["course_id"], x["rule"]) for x in recs] == [(nxt, "gratis_para_empezar")]

    # Monto insuficiente -> 400; pago correcto -> inscripción automática.
    # El precio premium incluye el recargo del Decorator (49.9 * 1.2).
    assert course["price"] == 59.88
    pay = {"amount": course["price"], "currency": "USD", "gateway": "stripe", "course_id": cid}
    assert client.post("/payments/process", json={**pay, "amount": 10},
                       headers=alum).status_code == 400
    r = client.post("/payments/process", json=pay, headers=alum)
    assert r.status_code == 200 and r.json()["status"] == "approved"
    assert client.post("/payments/process", json=pay, headers=alum).status_code == 409
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 409
    enrolled = client.get("/courses/me/enrolled", headers=alum).json()
    assert [c["id"] for c in enrolled] == [cid]

    # Contenido (Proxy) y resumen (Visitor).
    assert client.get(f"/courses/{cid}/content", headers=alum).status_code == 200
    summary = client.get(f"/courses/{cid}/content/summary", headers=alum).json()
    assert (summary["total_lessons"], summary["total_minutes"]) == (3, 60)

    # Clase grabada visible para el inscrito.
    sessions = client.get(f"/courses/{cid}/live-sessions", headers=alum).json()
    assert sessions[0]["recording_url"] == recorded["recording_url"]

    # Completar lecciones (progreso por Visitor).
    for i, lesson in enumerate(lessons, start=1):
        r = client.post(f"/courses/{cid}/lessons/{lesson}/complete", headers=alum)
        assert r.status_code == 200
    progress = client.get(f"/courses/{cid}/progress/me", headers=alum).json()
    assert progress["percentage"] == 100.0 and progress["completed_minutes"] == 60

    # Rendir evaluación (State): aprobado -> certificado (Observer).
    listed = client.get(f"/courses/{cid}/assessments", headers=alum).json()
    assert all("correct_option" not in q for q in listed[0]["questions"])
    r = client.post(f"/assessments/{aid}/attempts",
                    json={"answers": {q: 2 for q in qids}}, headers=alum)
    assert r.status_code == 201 and r.json()["passed"] is True
    certs = client.get("/certificates/me", headers=alum).json()
    assert [c["course_id"] for c in certs] == [cid]
    assert client.get(f"/certificates/verify/{certs[0]['verification_code']}").json()["valid"]

    # Notificaciones in-app del estudiante. La clase se grabó ANTES de que se
    # inscribiera, así que LIVE_SESSION_RECORDED no le llegó (se notifica a
    # los inscritos en el momento del evento).
    types = {n["event_type"] for n in client.get("/notifications/me", headers=alum).json()}
    assert {"payment_approved", "student_enrolled", "assessment_graded",
            "certificate_issued"} <= types
    assert "live_session_recorded" not in types

    # Perfil alimentado por el Observer y recomendación final.
    profile = container.learning_profile_repository.get_profile(alum_id)
    assert profile["enrolled_courses"] == [cid]
    assert sorted(profile["completed_lessons"][cid]) == sorted(lessons)
    assert profile["certificates"] == [cid]
    recs = client.get("/recommendations/me", headers=alum).json()
    assert recs[0]["course_id"] == nxt
    assert recs[0]["rule"] == "siguiente_nivel" and recs[0]["reason"]
    assert cid not in [x["course_id"] for x in recs]

    # ---------------------------------------------------------- autorización
    assert client.get("/recommendations/me").status_code == 401
    assert client.get("/notifications/me").status_code == 401
    assert client.post("/payments/process", json=pay).status_code == 401
    assert client.post("/assessments", json={"course_id": cid, "title": "X"},
                       headers=alum).status_code == 403
    assert client.post("/courses/", json={"title": "X", "price": 0, "course_type": "video"},
                       headers=alum).status_code == 403
    assert client.get("/admin/audit-log", headers=alum).status_code == 403
    assert client.get("/users/", headers=inst).status_code == 403
    assert client.post(f"/assessments/{aid}/publish", headers=inst).status_code == 409
    assert client.post(f"/live-sessions/{sid}/start", headers=inst).status_code == 409

    admin = _admin(client)
    audit = client.get("/admin/audit-log", headers=admin).json()
    audited = {e["event_type"] for e in audit}
    assert {"course_published", "payment_approved", "student_enrolled", "lesson_completed",
            "assessment_submitted", "assessment_graded", "certificate_issued",
            "live_session_recorded"} <= audited

    health = client.get("/health").json()["counters"]
    assert health["certificates"] == 1 and health["payments"] == 1


# ------------------------------------------------------------------ seed

def _test_client_requester(client):
    def request(method, path, body=None, token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = client.request(method, path, json=body, headers=headers)
        return r.status_code, (r.json() if r.content else None)
    return request


def test_seed_crea_la_demo_y_es_idempotente(client):
    session_factory = lambda: next(app.dependency_overrides[get_db]())  # noqa: E731
    request = _test_client_requester(client)
    logs = []

    first = seed.run_seed(request, create_admin=lambda: seed.ensure_admin(session_factory),
                          log=logs.append)
    assert first["assessment_id"] and first["live_session_id"]
    second = seed.run_seed(request, create_admin=lambda: seed.ensure_admin(session_factory),
                           log=logs.append)
    assert second["premium_course_id"] == first["premium_course_id"]
    assert second["free_course_id"] == first["free_course_id"]
    assert second["assessment_id"] is None            # no duplica evaluación/clase
    assert len(client.get("/courses/").json()) == 2

    # Las cuentas demo funcionan con la contraseña documentada.
    for email in (seed.ADMIN["email"], seed.INSTRUCTOR["email"], seed.STUDENT["email"]):
        r = client.post("/auth/login", json={"email": email, "password": seed.DEMO_PASSWORD})
        assert r.status_code == 200, email

    token = client.post("/auth/login", json={"email": seed.STUDENT["email"],
                        "password": seed.DEMO_PASSWORD}).json()["access_token"]
    alum = {"Authorization": f"Bearer {token}"}
    pid = first["premium_course_id"]
    progress = client.get(f"/courses/{first['free_course_id']}/progress/me", headers=alum).json()
    assert progress["completed_lessons"] == 1
    recs = client.get("/recommendations/me", headers=alum).json()
    assert recs[0]["course_id"] == pid                # afinidad con el curso gratuito

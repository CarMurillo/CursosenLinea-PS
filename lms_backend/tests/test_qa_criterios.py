"""
Pruebas de QA independientes (Fase 5) para cerrar huecos de la sección 6
de PROMPT_CLAUDE_CODE.md:

- State: matriz COMPLETA de transiciones inválidas por API -> 409
  (evaluaciones y clases en vivo).
- Observer: un único bus compartido por todos los casos de uso.
- Visitor/Proxy por API: progreso 0 % / parcial / 100 % y bloqueo del
  resumen y del progreso para quien no tiene acceso.
- Arquitectura: dominio sin FastAPI/SQLAlchemy/infraestructura y sin
  `isinstance` en el Composite/Visitor/estados (guardas de regresión).
- Seguridad: aislamiento entre usuarios (IDOR) e identidad tomada del token.
"""

import ast
import pathlib

import pytest

from app.main import app
from app.modules.auth.application.dtos import UserRegisterDTO
from app.modules.auth.application.use_cases import RegisterUserUseCase
from app.modules.auth.domain.models import Role
from app.shared.infrastructure import container
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository

PWD = "Secreta123"
APP_DIR = pathlib.Path(__file__).resolve().parents[1] / "app"


# ================================================================ utilidades

def _login(client, email, role="student", first="Ana", last="Perez"):
    r = client.post("/auth/register", json={
        "first_name": first, "last_name": last, "email": email,
        "password": PWD, "role": role})
    assert r.status_code == 201, r.text
    r = client.post("/auth/login", json={"email": email, "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _admin(client):
    db = next(app.dependency_overrides[get_db]())
    RegisterUserUseCase(SqlAlchemyUserRepository(db)).execute(UserRegisterDTO(
        first_name="Ad", last_name="Min", email="admin@qa.com", password=PWD,
        role=Role.ADMIN))
    r = client.post("/auth/login", json={"email": "admin@qa.com", "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _course(client, inst, **extra):
    body = {"title": "Curso QA", "price": 0, "course_type": "video", **extra}
    r = client.post("/courses/", json=body, headers=inst)
    assert r.status_code == 201, r.text
    return r.json()


def _lesson(client, cid, inst, title, minutes=10, module="M1"):
    r = client.post(f"/courses/{cid}/content/lessons", json={
        "module_title": module, "title": title, "media_id": title,
        "provider": "s3", "lesson_type": "video",
        "duration_minutes": minutes}, headers=inst)
    assert r.status_code == 201, r.text
    return r.json()["lesson_id"]


@pytest.fixture
def setup(client):
    inst = _login(client, "inst@qa.com", "instructor")
    alum = _login(client, "alum@qa.com", "student", "Luis", "Gomez")
    cid = _course(client, inst)["id"]
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 200
    return client, inst, alum, cid


# ============================================ State: matriz inválida por API

def _new_assessment(client, cid, inst, questions=1):
    r = client.post("/assessments", json={"course_id": cid, "title": "QA"},
                    headers=inst)
    assert r.status_code == 201
    aid = r.json()["id"]
    qids = []
    for i in range(questions):
        r = client.post(f"/assessments/{aid}/questions", json={
            "text": f"P{i}", "options": ["a", "b"], "correct_option": 0},
            headers=inst)
        assert r.status_code == 201
        qids.append(r.json()["question_id"])
    return aid, qids


_QUESTION = {"text": "Nueva", "options": ["a", "b"], "correct_option": 0}


@pytest.mark.parametrize("state, action", [
    ("draft_empty", "publish"),
    ("draft", "attempt"),
    ("draft", "close"),
    ("published", "question"),
    ("published", "publish"),
    ("closed", "question"),
    ("closed", "publish"),
    ("closed", "attempt"),
    ("closed", "close"),
])
def test_qa_evaluacion_toda_transicion_invalida_responde_409(setup, state, action):
    client, inst, alum, cid = setup
    aid, qids = _new_assessment(client, cid, inst,
                                questions=0 if state == "draft_empty" else 1)
    if state in ("published", "closed"):
        assert client.post(f"/assessments/{aid}/publish", headers=inst).status_code == 200
    if state == "closed":
        assert client.post(f"/assessments/{aid}/close", headers=inst).status_code == 200

    calls = {
        "publish": lambda: client.post(f"/assessments/{aid}/publish", headers=inst),
        "close": lambda: client.post(f"/assessments/{aid}/close", headers=inst),
        "question": lambda: client.post(f"/assessments/{aid}/questions",
                                        json=_QUESTION, headers=inst),
        "attempt": lambda: client.post(f"/assessments/{aid}/attempts",
                                       json={"answers": {q: 0 for q in qids}},
                                       headers=alum),
    }
    r = calls[action]()
    assert r.status_code == 409, r.text
    assert r.json()["detail"]                       # mensaje claro
    # La transición inválida no cambia el estado.
    expected = "draft" if state.startswith("draft") else state
    assert client.get(f"/assessments/{aid}", headers=inst).json()["state"] == expected


@pytest.mark.parametrize("steps, action", [
    ([], "end"),
    (["start"], "start"),
    (["start", "end"], "start"),
    (["start", "end"], "end"),
])
def test_qa_clase_en_vivo_toda_transicion_invalida_responde_409(setup, steps, action):
    client, inst, _alum, cid = setup
    sid = client.post("/live-sessions", json={"course_id": cid, "title": "C"},
                      headers=inst).json()["id"]
    for step in steps:
        assert client.post(f"/live-sessions/{sid}/{step}", headers=inst).status_code == 200
    before = client.get(f"/live-sessions/{sid}", headers=inst).json()["state"]
    r = client.post(f"/live-sessions/{sid}/{action}", headers=inst)
    assert r.status_code == 409 and r.json()["detail"]
    assert client.get(f"/live-sessions/{sid}", headers=inst).json()["state"] == before


def test_qa_calificacion_automatica_parcial_por_api(setup):
    client, inst, alum, cid = setup
    aid, qids = _new_assessment(client, cid, inst, questions=4)
    client.post(f"/assessments/{aid}/publish", headers=inst)
    answers = {qids[0]: 0, qids[1]: 0, qids[2]: 1}      # 2 de 4 correctas
    r = client.post(f"/assessments/{aid}/attempts", json={"answers": answers},
                    headers=alum)
    assert r.status_code == 201
    body = r.json()
    assert (body["score"], body["max_score"], body["percentage"], body["passed"]) \
        == (2, 4, 50.0, False)
    assert body["user_id"] != "" and body["attempt_number"] == 1


# ===================================================== Observer: bus único

def test_qa_un_solo_bus_compartido_por_todos_los_casos_de_uso():
    bus = container.event_bus
    assert container.make_assessment_service()._event_bus is bus
    assert container.make_live_session_service()._event_bus is bus
    assert container.make_process_payment_use_case().event_bus is bus
    assert container.make_complete_lesson_use_case().event_bus is bus
    assert container.course_facade._event_bus is bus
    # Llamadas repetidas no crean buses nuevos.
    assert container.make_assessment_service()._event_bus is \
        container.make_assessment_service()._event_bus


def test_qa_reset_reutiliza_la_misma_instancia_de_bus():
    bus = container.event_bus
    container.reset_state()
    assert container.event_bus is bus
    # Seis observadores por defecto, sin duplicados tras re-cablear.
    assert len(bus.observers) == 6
    assert len({id(o) for o in bus.observers}) == 6


def test_qa_detach_de_observador_no_adjuntado_es_inocuo():
    from app.shared.domain.events import DomainEvent, EventType, Observer, Subject

    class Rec(Observer):
        def __init__(self):
            self.n = 0

        def update(self, event):
            self.n += 1

    bus, a = Subject(), Rec()
    bus.detach(a)                      # no lanza
    bus.attach(a)
    bus.attach(a)                      # no duplica
    bus.notify(DomainEvent(EventType.COURSE_PUBLISHED))
    assert a.n == 1
    bus.detach(a)
    bus.notify(DomainEvent(EventType.COURSE_PUBLISHED))
    assert a.n == 1


# ===================================================== Visitor/Proxy por API

def test_qa_progreso_0_parcial_100_por_api(setup):
    client, inst, alum, cid = setup
    l1 = _lesson(client, cid, inst, "L1", 10)
    l2 = _lesson(client, cid, inst, "L2", 30, module="M2")

    p = client.get(f"/courses/{cid}/progress/me", headers=alum).json()
    assert (p["percentage"], p["completed_lessons"], p["total_lessons"],
            p["total_minutes"]) == (0.0, 0, 2, 40)

    client.post(f"/courses/{cid}/lessons/{l2}/complete", headers=alum)
    p = client.get(f"/courses/{cid}/progress/me", headers=alum).json()
    assert (p["percentage"], p["completed_minutes"]) == (50.0, 30)

    client.post(f"/courses/{cid}/lessons/{l1}/complete", headers=alum)
    p = client.get(f"/courses/{cid}/progress/me", headers=alum).json()
    assert p["percentage"] == 100.0 and sorted(p["completed_lesson_ids"]) == sorted([l1, l2])

    s = client.get(f"/courses/{cid}/content/summary", headers=alum).json()
    assert (s["total_modules"], s["total_lessons"], s["total_minutes"]) == (2, 2, 40)
    assert s["lessons_by_type"] == {"video": 2}


def test_qa_proxy_bloquea_resumen_y_progreso_en_premium_sin_pago(client):
    inst = _login(client, "inst@qa.com", "instructor")
    alum = _login(client, "alum@qa.com")
    cid = _course(client, inst, price=20, premium=True)["id"]
    lid = _lesson(client, cid, inst, "L1")

    for method, url in [
        ("get", f"/courses/{cid}/content"),
        ("get", f"/courses/{cid}/content/summary"),
        ("get", f"/courses/{cid}/progress/me"),
        ("post", f"/courses/{cid}/lessons/{lid}/complete"),
        ("get", f"/courses/{cid}/assessments"),
        ("get", f"/courses/{cid}/live-sessions"),
    ]:
        r = getattr(client, method)(url, headers=alum)
        assert r.status_code == 403, (url, r.status_code)
    assert client.get("/courses/me/enrolled", headers=alum).json() == []
    # El dueño sí pasa por el Proxy.
    assert client.get(f"/courses/{cid}/content/summary", headers=inst).status_code == 200


# =============================================== Arquitectura (regresión)

_FORBIDDEN_IN_DOMAIN = ("fastapi", "sqlalchemy", "starlette", "pydantic")


def _domain_files(root):
    return [p for p in root.rglob("*.py") if "domain" in p.parts]


def _domain_offenders(root):
    offenders = []
    for path in _domain_files(root):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.split(".")[0] in _FORBIDDEN_IN_DOMAIN or ".infrastructure" in name:
                    offenders.append(f"{path.relative_to(APP_DIR)}: {name}")
    return offenders


def test_qa_dominio_de_modulos_y_shared_es_puro():
    """modules/*/domain y shared/domain: sin FastAPI/SQLAlchemy/infraestructura."""
    assert _domain_offenders(APP_DIR / "modules") == []
    assert _domain_offenders(APP_DIR / "shared") == []


def test_qa6_dominio_de_usuarios_no_importa_infraestructura():
    assert _domain_offenders(APP_DIR / "users") == []


_NO_ISINSTANCE = [
    "modules/courses/domain/visitor.py",
    "modules/courses/domain/composite.py",
    "modules/courses/domain/bridge.py",
    "modules/courses/domain/content_proxy.py",
    "modules/assessments/domain/states.py",
    "modules/assessments/domain/models.py",
    "modules/live_sessions/domain/states.py",
    "modules/live_sessions/domain/models.py",
    "modules/progress/application/use_cases.py",
    "modules/courses/infrastructure/api.py",
]


@pytest.mark.parametrize("rel", _NO_ISINSTANCE)
def test_qa_sin_isinstance_en_composite_visitor_y_estados(rel):
    tree = ast.parse((APP_DIR / rel).read_text(encoding="utf-8"))
    calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "isinstance"
    ]
    assert calls == [], rel


def test_qa_estados_no_comparan_nombre_de_estado():
    """Ni el contexto ni los servicios preguntan `state == ...`."""
    for rel in ["modules/assessments/domain/models.py",
                "modules/assessments/application/use_cases.py",
                "modules/live_sessions/domain/models.py",
                "modules/live_sessions/application/use_cases.py"]:
        tree = ast.parse((APP_DIR / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                for side in [node.left, *node.comparators]:
                    if isinstance(side, ast.Constant) and side.value in (
                        "draft", "published", "closed", "scheduled", "live",
                        "ended", "recorded",
                    ):
                        pytest.fail(f"{rel}:{node.lineno} compara estado por nombre")


# ========================================================= Seguridad / IDOR

def test_qa_datos_personales_aislados_entre_usuarios(client):
    inst = _login(client, "inst@qa.com", "instructor")
    ana = _login(client, "ana@qa.com", "student", "Ana", "A")
    beto = _login(client, "beto@qa.com", "student", "Beto", "B")
    cid = _course(client, inst, price=15, certificate=True)["id"]

    r = client.post("/payments/process", json={
        "amount": 15, "currency": "USD", "gateway": "stripe", "course_id": cid},
        headers=ana)
    assert r.status_code == 200

    assert len(client.get("/payments/me", headers=ana).json()) == 1
    assert client.get("/payments/me", headers=beto).json() == []
    assert client.get("/notifications/me", headers=ana).json() != []
    assert client.get("/notifications/me", headers=beto).json() == []
    assert client.get("/courses/me/enrolled", headers=beto).json() == []
    # Beto no ve contenido ni progreso del curso que pagó Ana.
    assert client.get(f"/courses/{cid}/content", headers=beto).status_code == 403
    assert client.get(f"/courses/{cid}/progress/me", headers=beto).status_code == 403


def test_qa_pago_ignora_user_id_del_cuerpo(client):
    inst = _login(client, "inst@qa.com", "instructor")
    ana = _login(client, "ana@qa.com", "student", "Ana", "A")
    beto = _login(client, "beto@qa.com", "student", "Beto", "B")
    assert client.get("/payments/me", headers=beto).status_code == 200
    cid = _course(client, inst, price=10)["id"]

    r = client.post("/payments/process", json={
        "amount": 10, "currency": "USD", "gateway": "stripe", "course_id": cid,
        "user_id": "otro", "customer_email": "x@evil.com"}, headers=ana)
    assert r.status_code == 200
    assert client.get("/payments/me", headers=beto).json() == []
    pagos = client.get("/payments/me", headers=ana).json()
    assert len(pagos) == 1 and pagos[0]["user_id"] != "otro"


def test_qa_estudiante_no_escala_a_staff(setup):
    client, _inst, alum, cid = setup
    assert client.post("/courses/", json={"title": "x", "price": 0,
                       "course_type": "video"}, headers=alum).status_code == 403
    assert client.post(f"/courses/{cid}/clone", json={}, headers=alum).status_code == 403
    assert client.post(f"/courses/{cid}/content/lessons", json={
        "module_title": "M", "title": "L", "media_id": "1", "provider": "s3"},
        headers=alum).status_code == 403
    assert client.post("/live-sessions", json={"course_id": cid, "title": "x"},
                       headers=alum).status_code == 403
    assert client.get("/admin/audit-log", headers=alum).status_code == 403
    assert client.get("/users/", headers=alum).status_code == 403


def test_qa_admin_gestiona_curso_ajeno(setup):
    client, _inst, _alum, cid = setup
    admin = _admin(client)
    assert client.post(f"/courses/{cid}/clone", json={}, headers=admin).status_code == 201
    r = client.post("/assessments", json={"course_id": cid, "title": "A"}, headers=admin)
    assert r.status_code == 201


@pytest.mark.parametrize("method, url", [
    ("get", "/courses/me/enrolled"),
    ("get", "/notifications/me"),
    ("get", "/payments/me"),
    ("get", "/certificates/me"),
    ("get", "/recommendations/me"),
    ("get", "/admin/audit-log"),
    ("get", "/users/"),
    ("post", "/payments/process"),
    ("post", "/courses/"),
    ("post", "/assessments"),
    ("post", "/live-sessions"),
])
def test_qa_rutas_privadas_exigen_token(client, method, url):
    assert getattr(client, method)(url).status_code == 401


def test_qa_token_invalido_401(client):
    r = client.get("/notifications/me", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401
    r = client.get("/notifications/me", headers={"Authorization": "Basic abc"})
    assert r.status_code == 401

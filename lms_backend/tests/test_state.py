"""Pruebas del patrón State: evaluaciones, clases en vivo y certificados."""

import pytest

from app.main import app
from app.modules.assessments.application.use_cases import AssessmentService
from app.modules.assessments.domain.models import (
    Assessment,
    AttemptLimitReached,
    Question,
)
from app.modules.assessments.domain.states import (
    AssessmentState,
    ClosedState,
    DraftState,
    PublishedState,
)
from app.modules.assessments.infrastructure.repository import (
    InMemoryAssessmentRepository,
)
from app.modules.auth.application.dtos import UserRegisterDTO
from app.modules.auth.application.use_cases import RegisterUserUseCase
from app.modules.auth.domain.models import Role
from app.modules.certificates.application.services import CertificateService
from app.modules.certificates.infrastructure.repository import (
    InMemoryCertificateRepository,
)
from app.modules.live_sessions.application.use_cases import LiveSessionService
from app.modules.live_sessions.domain.models import LiveSession
from app.modules.live_sessions.domain.states import (
    EndedState,
    LiveState,
    RecordedState,
    ScheduledState,
)
from app.modules.live_sessions.infrastructure.jitsi_adapter import JitsiAdapter
from app.modules.live_sessions.infrastructure.repository import (
    InMemoryLiveSessionRepository,
)
from app.shared.domain.errors import PermissionDenied
from app.shared.domain.events import EventType, Observer, Subject
from app.shared.domain.state import CourseInfo, InvalidStateTransition
from app.shared.infrastructure import container
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository

PWD = "Secreta123"


# ================================================================ helpers

class Recorder(Observer):
    def __init__(self):
        self.events = []

    def update(self, event):
        self.events.append(event)


class FakeCatalog:
    def __init__(self, *courses: CourseInfo):
        self._courses = {c.course_id: c for c in courses}

    def get_course_info(self, course_id):
        return self._courses.get(course_id)


def _question(points=1.0, correct=1):
    return Question("¿2 + 2?", ["3", "4", "5"], correct, points)


def _published(questions=2, **kw):
    a = Assessment("c1", "Parcial", created_by="inst", **kw)
    for _ in range(questions):
        a.add_question(_question())
    a.publish()
    return a


# ============================================ evaluaciones: transiciones válidas

def test_borrador_por_defecto_y_agrega_preguntas():
    a = Assessment("c1", "Parcial", created_by="inst")
    assert isinstance(a.state, DraftState) and a.state_name == "draft"
    a.add_question(_question())
    assert len(a.questions) == 1 and not a.visible_to_students


def test_draft_a_published_a_closed():
    a = Assessment("c1", "Parcial", created_by="inst")
    a.add_question(_question())
    a.publish()
    assert isinstance(a.state, PublishedState) and a.visible_to_students
    a.close()
    assert isinstance(a.state, ClosedState) and a.state_name == "closed"


# ========================================== evaluaciones: transiciones inválidas

def test_publicar_sin_preguntas_es_invalido():
    a = Assessment("c1", "Parcial", created_by="inst")
    with pytest.raises(InvalidStateTransition, match="al menos una pregunta"):
        a.publish()
    assert a.state_name == "draft"


@pytest.mark.parametrize("make, action", [
    (lambda: Assessment("c1", "P", created_by="i"), lambda a: a.submit_attempt("u", {})),
    (lambda: Assessment("c1", "P", created_by="i"), lambda a: a.close()),
    (_published, lambda a: a.add_question(_question())),
    (_published, lambda a: a.publish()),
    (lambda: _closed(), lambda a: a.add_question(_question())),
    (lambda: _closed(), lambda a: a.publish()),
    (lambda: _closed(), lambda a: a.submit_attempt("u", {})),
    (lambda: _closed(), lambda a: a.close()),
])
def test_transiciones_invalidas_lanzan_excepcion(make, action):
    a = make()
    before = a.state_name
    with pytest.raises(InvalidStateTransition) as info:
        action(a)
    assert info.value.state == before
    assert a.state_name == before            # el estado no cambia


def _closed():
    a = _published()
    a.close()
    return a


# =================================================== evaluaciones: calificación

def test_calificacion_automatica_y_umbral():
    a = Assessment("c1", "Parcial", created_by="inst", passing_score=60, max_attempts=2)
    q1 = a.add_question(_question(points=3, correct=1))
    q2 = a.add_question(_question(points=1, correct=0))
    a.publish()

    fail = a.submit_attempt("u1", {q2.question_id: 0})
    assert (fail.score, fail.max_score, fail.percentage, fail.passed) == (1, 4, 25.0, False)

    ok = a.submit_attempt("u1", {q1.question_id: 1, q2.question_id: 2})
    assert (ok.score, ok.percentage, ok.passed, ok.attempt_number) == (3, 75.0, True, 2)

    with pytest.raises(AttemptLimitReached):
        a.submit_attempt("u1", {})
    assert len(a.attempts_of("u1")) == 2


def test_respuesta_a_pregunta_desconocida_es_error_de_validacion():
    a = _published()
    with pytest.raises(ValueError):
        a.submit_attempt("u1", {"no-existe": 0})


def test_nuevo_estado_solo_requiere_una_clase():
    """Extensibilidad: un estado nuevo se conecta sin tocar el contexto."""

    class ArchivedState(ClosedState):
        name = "archived"
        visible_to_students = False

    class ClosableToArchive(PublishedState):
        def close(self, assessment):
            assessment._transition_to(ArchivedState())

    a = Assessment("c1", "P", created_by="i", state=ClosableToArchive())
    a.close()
    assert a.state_name == "archived" and not a.visible_to_students
    with pytest.raises(InvalidStateTransition):
        a.submit_attempt("u", {})
    assert issubclass(ArchivedState, AssessmentState)


def test_servicio_publica_submitted_y_graded_con_contrato():
    bus, seen = Subject(), Recorder()
    bus.attach(seen)
    course = CourseInfo("c1", "Python", "inst", frozenset({"alum"}), True)
    service = AssessmentService(InMemoryAssessmentRepository(), FakeCatalog(course), bus)
    a = service.create(course_id="c1", title="Final", user_id="inst", role="instructor")
    q = service.add_question(a.assessment_id, user_id="inst", role="instructor",
                             text="?", options=["a", "b"], correct_option=0, points=2)
    service.publish(a.assessment_id, user_id="inst", role="instructor")

    with pytest.raises(PermissionDenied):
        service.submit_attempt(a.assessment_id, user_id="intruso", answers={})
    attempt = service.submit_attempt(a.assessment_id, user_id="alum",
                                     answers={q.question_id: 0})

    submitted, graded = seen.events
    assert submitted.event_type == EventType.ASSESSMENT_SUBMITTED
    assert dict(submitted.payload) == {"assessment_id": a.assessment_id,
                                       "attempt_id": attempt.attempt_id}
    assert graded.event_type == EventType.ASSESSMENT_GRADED
    assert graded.user_id == "alum" and graded.course_id == "c1"
    for key, value in {"assessment_id": a.assessment_id, "score": 2.0, "passed": True,
                       "course_title": "Python", "max_score": 2.0}.items():
        assert graded.payload[key] == value


# =========================================================== certificados

def test_certificado_solo_si_curso_lo_otorga_e_idempotente():
    catalog = FakeCatalog(CourseInfo("c1", "Py", "i", has_certificate=True),
                          CourseInfo("c2", "Js", "i", has_certificate=False))
    service = CertificateService(InMemoryCertificateRepository(), catalog)
    first = service.issue("u1", "c1", {"score": 9, "assessment_id": "a1"})
    assert first["certificate_id"] and first["verification_code"].startswith("LMS-")
    assert first["course_title"] == "Py"
    assert service.issue("u1", "c1", {"score": 10}) is None      # ya existe
    assert service.issue("u1", "c2", {"score": 10}) is None      # sin certificado
    assert service.issue("u1", "nope", {}) is None               # curso inexistente
    assert [c.course_id for c in service.list_by_user("u1")] == ["c1"]
    assert service.verify(first["verification_code"].lower()).user_id == "u1"


# ================================================= clases en vivo (unitarias)

def _session(adapter):
    room_name, room_url = adapter.create_room("1234abcd-0000", "Clase de Álgebra")
    return LiveSession("c1", "Clase de Álgebra", instructor_id="inst",
                       room_name=room_name, room_url=room_url, provider="jitsi")


def test_ciclo_completo_clase_en_vivo_con_url_de_grabacion():
    jitsi = JitsiAdapter()
    s = _session(jitsi)
    assert isinstance(s.state, ScheduledState)
    assert s.room_url == "https://meet.jit.si/lms-clase-de-algebra-1234abcd"
    s.start(jitsi)
    assert isinstance(s.state, LiveState) and s.started_at is not None
    assert jitsi.meeting_status(s.room_name) == "live"
    s.end(jitsi)
    assert isinstance(s.state, EndedState) and s.ended_at is not None
    s.record(jitsi)
    assert isinstance(s.state, RecordedState)
    assert s.recording_url == (
        "https://recordings.lms.local/jitsi/lms-clase-de-algebra-1234abcd.mp4")


@pytest.mark.parametrize("steps, action", [
    ([], "end"), ([], "record"),
    (["start"], "start"), (["start"], "record"),
    (["start", "end"], "start"), (["start", "end"], "end"),
    (["start", "end", "record"], "start"), (["start", "end", "record"], "end"),
    (["start", "end", "record"], "record"),
])
def test_transiciones_invalidas_clase_en_vivo(steps, action):
    jitsi = JitsiAdapter()
    s = _session(jitsi)
    for step in steps:
        getattr(s, step)(jitsi)
    before = s.state_name
    with pytest.raises(InvalidStateTransition):
        getattr(s, action)(jitsi)
    assert s.state_name == before


def test_servicio_live_publica_live_session_recorded():
    bus, seen = Subject(), Recorder()
    bus.attach(seen, [EventType.LIVE_SESSION_RECORDED])
    catalog = FakeCatalog(CourseInfo("c1", "Py", "inst", frozenset({"alum"})))
    service = LiveSessionService(InMemoryLiveSessionRepository(), catalog, JitsiAdapter(), bus)
    s = service.schedule(course_id="c1", title="Clase 1", user_id="inst", role="instructor")
    service.start(s.session_id, user_id="inst", role="instructor")
    service.end(s.session_id, user_id="inst", role="instructor")
    (event,) = seen.events
    assert event.user_id == "inst" and event.course_id == "c1"
    assert event.payload["session_id"] == s.session_id
    assert event.payload["session_title"] == "Clase 1"
    assert s.recording_url and event.payload["recording_url"] == s.recording_url


# ===================================================================== API

def _login(client, email, role, first="Ana", last="Perez"):
    client.post("/auth/register", json={"first_name": first, "last_name": last,
                "email": email, "password": PWD, "role": role})
    r = client.post("/auth/login", json={"email": email, "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _admin(client):
    db = next(app.dependency_overrides[get_db]())
    RegisterUserUseCase(SqlAlchemyUserRepository(db)).execute(UserRegisterDTO(
        first_name="Ad", last_name="Min", email="admin@x.com", password=PWD,
        role=Role.ADMIN))
    r = client.post("/auth/login", json={"email": "admin@x.com", "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _course(client, inst, certificate=True):
    r = client.post("/courses/", json={"title": "Python", "price": 0,
                    "course_type": "video", "certificate": certificate}, headers=inst)
    assert r.status_code == 201
    return r.json()["id"]


def _enroll(client, cid, alum):
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 200


def _assessment(client, cid, inst, questions=2, **extra):
    r = client.post("/assessments", json={"course_id": cid, "title": "Parcial 1",
                    "passing_score": 60, **extra}, headers=inst)
    assert r.status_code == 201, r.text
    aid = r.json()["id"]
    qids = []
    for i in range(questions):
        r = client.post(f"/assessments/{aid}/questions", json={
            "text": f"Pregunta {i}", "options": ["a", "b", "c"],
            "correct_option": 1, "points": 5}, headers=inst)
        assert r.status_code == 201
        qids.append(r.json()["question_id"])
    return aid, qids


@pytest.fixture
def actors(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student", "Luis", "Gomez")
    cid = _course(client, inst)
    _enroll(client, cid, alum)
    return client, inst, alum, cid


def test_api_ciclo_evaluacion_y_409(actors):
    client, inst, alum, cid = actors
    aid, qids = _assessment(client, cid, inst)
    answers = {"answers": {q: 1 for q in qids}}

    # Borrador: invisible para el estudiante y sin intentos.
    assert client.get(f"/courses/{cid}/assessments", headers=alum).json() == []
    assert client.get(f"/assessments/{aid}", headers=alum).status_code == 404
    r = client.post(f"/assessments/{aid}/attempts", json=answers, headers=alum)
    assert r.status_code == 409 and "draft" in r.json()["detail"]
    assert client.post(f"/assessments/{aid}/close", headers=inst).status_code == 409

    r = client.post(f"/assessments/{aid}/publish", headers=inst)
    assert r.status_code == 200 and r.json()["state"] == "published"
    assert client.post(f"/assessments/{aid}/publish", headers=inst).status_code == 409
    r = client.post(f"/assessments/{aid}/questions", json={
        "text": "Tarde", "options": ["a", "b"], "correct_option": 0}, headers=inst)
    assert r.status_code == 409

    # El estudiante ve la evaluación publicada SIN respuestas correctas.
    listed = client.get(f"/courses/{cid}/assessments", headers=alum).json()
    assert [a["id"] for a in listed] == [aid]
    assert all("correct_option" not in q for q in listed[0]["questions"])
    owner_view = client.get(f"/assessments/{aid}", headers=inst).json()
    assert all("correct_option" in q for q in owner_view["questions"])

    r = client.post(f"/assessments/{aid}/close", headers=inst)
    assert r.status_code == 200 and r.json()["state"] == "closed"
    assert client.post(f"/assessments/{aid}/close", headers=inst).status_code == 409
    assert client.post(f"/assessments/{aid}/publish", headers=inst).status_code == 409
    r = client.post(f"/assessments/{aid}/attempts", json=answers, headers=alum)
    assert r.status_code == 409 and "cerrada" in r.json()["detail"]


def test_api_aprobar_emite_certificado_una_sola_vez(actors):
    client, inst, alum, cid = actors
    aid, qids = _assessment(client, cid, inst, max_attempts=3)
    client.post(f"/assessments/{aid}/publish", headers=inst)

    r = client.post(f"/assessments/{aid}/attempts", json={"answers": {qids[0]: 0}},
                    headers=alum)
    assert r.status_code == 201
    assert (r.json()["score"], r.json()["passed"]) == (0, False)
    assert client.get("/certificates/me", headers=alum).json() == []

    ok = {"answers": {q: 1 for q in qids}}
    for _ in range(2):  # aprobar dos veces no duplica el certificado
        r = client.post(f"/assessments/{aid}/attempts", json=ok, headers=alum)
        assert r.status_code == 201
        body = r.json()
        assert (body["score"], body["max_score"], body["percentage"], body["passed"]) \
            == (10, 10, 100.0, True)
    r = client.post(f"/assessments/{aid}/attempts", json=ok, headers=alum)
    assert r.status_code == 409   # límite de intentos

    certs = client.get("/certificates/me", headers=alum).json()
    assert len(certs) == 1
    assert certs[0]["course_id"] == cid and certs[0]["score"] == 10
    assert client.get("/certificates/me", headers=inst).json() == []
    code = certs[0]["verification_code"]
    v = client.get(f"/certificates/verify/{code}")
    assert v.status_code == 200 and v.json()["valid"] and "user_id" not in v.json()

    mine = client.get(f"/assessments/{aid}", headers=alum).json()
    assert len(mine["my_attempts"]) == 3
    types = [n["event_type"] for n in client.get("/notifications/me", headers=alum).json()]
    assert types.count("certificate_issued") == 1
    assert types.count("assessment_graded") == 3


def test_api_curso_sin_certificado_no_emite(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    cid = _course(client, inst, certificate=False)
    _enroll(client, cid, alum)
    aid, qids = _assessment(client, cid, inst)
    client.post(f"/assessments/{aid}/publish", headers=inst)
    r = client.post(f"/assessments/{aid}/attempts",
                    json={"answers": {q: 1 for q in qids}}, headers=alum)
    assert r.json()["passed"] is True
    assert client.get("/certificates/me", headers=alum).json() == []


def test_api_autorizacion_evaluaciones(actors):
    client, inst, alum, cid = actors
    otro_inst = _login(client, "o@x.com", "instructor")
    intruso = _login(client, "x@x.com", "student")
    body = {"course_id": cid, "title": "Quiz"}

    assert client.post("/assessments", json=body).status_code == 401
    assert client.get("/certificates/me").status_code == 401
    assert client.post("/assessments", json=body, headers=alum).status_code == 403
    assert client.post("/assessments", json=body, headers=otro_inst).status_code == 403
    assert client.post("/assessments", json={**body, "course_id": "nope"},
                       headers=inst).status_code == 404
    assert client.post("/assessments", json={**body, "passing_score": 150},
                       headers=inst).status_code == 422

    aid, qids = _assessment(client, cid, inst)
    assert client.post(f"/assessments/{aid}/publish", headers=otro_inst).status_code == 403
    assert client.post(f"/assessments/{aid}/publish", headers=alum).status_code == 403
    r = client.post(f"/assessments/{aid}/questions", json={
        "text": "x", "options": ["solo una"], "correct_option": 0}, headers=inst)
    assert r.status_code == 422
    r = client.post(f"/assessments/{aid}/questions", json={
        "text": "x", "options": ["a", "b"], "correct_option": 5}, headers=inst)
    assert r.status_code == 422
    assert client.post(f"/assessments/{aid}/publish", headers=_admin(client)).status_code == 200

    answers = {"answers": {q: 1 for q in qids}}
    assert client.post(f"/assessments/{aid}/attempts", json=answers,
                       headers=intruso).status_code == 403
    assert client.post(f"/assessments/{aid}/attempts", json=answers,
                       headers=inst).status_code == 403   # el instructor no rinde
    assert client.post("/assessments/nope/attempts", json=answers,
                       headers=alum).status_code == 404
    assert client.post(f"/assessments/{aid}/attempts", json={"answers": {"zzz": 1}},
                       headers=alum).status_code == 422
    assert client.get(f"/courses/{cid}/assessments", headers=intruso).status_code == 403
    assert client.get(f"/assessments/{aid}", headers=intruso).status_code == 403
    assert client.get("/courses/nope/assessments", headers=alum).status_code == 404


def test_api_clase_en_vivo_ciclo_completo_y_notificacion(actors):
    client, inst, alum, cid = actors
    r = client.post("/live-sessions", json={"course_id": cid, "title": "Clase 1",
                    "scheduled_at": "2099-12-01T15:00:00Z"}, headers=inst)
    assert r.status_code == 201
    session = r.json()
    sid = session["id"]
    assert session["state"] == "scheduled" and session["recording_url"] is None
    assert session["room_url"].startswith("https://meet.jit.si/lms-clase-1-")

    assert client.post(f"/live-sessions/{sid}/end", headers=inst).status_code == 409
    r = client.post(f"/live-sessions/{sid}/start", headers=inst)
    assert r.status_code == 200 and r.json()["state"] == "live"
    assert client.post(f"/live-sessions/{sid}/start", headers=inst).status_code == 409

    r = client.post(f"/live-sessions/{sid}/end", headers=inst)
    assert r.status_code == 200
    ended = r.json()
    assert ended["state"] == "recorded"
    assert ended["recording_url"].startswith("https://recordings.lms.local/jitsi/lms-clase-1-")
    assert ended["recording_url"].endswith(".mp4")
    r = client.post(f"/live-sessions/{sid}/end", headers=inst)
    assert r.status_code == 409 and "recorded" in r.json()["detail"]
    assert client.post(f"/live-sessions/{sid}/start", headers=inst).status_code == 409

    listed = client.get(f"/courses/{cid}/live-sessions", headers=alum).json()
    assert [s["id"] for s in listed] == [sid]
    assert client.get(f"/live-sessions/{sid}", headers=alum).json()["recording_url"] \
        == ended["recording_url"]

    notes = client.get("/notifications/me", headers=alum).json()
    recorded = [n for n in notes if n["event_type"] == "live_session_recorded"]
    assert len(recorded) == 1 and "Clase 1" in recorded[0]["message"]
    audit = container.audit_log_repository.list_entries(
        event_type="live_session_recorded")
    assert len(audit) == 1


def test_api_autorizacion_clases_en_vivo(actors):
    client, inst, alum, cid = actors
    otro_inst = _login(client, "o@x.com", "instructor")
    intruso = _login(client, "x@x.com", "student")
    body = {"course_id": cid, "title": "Clase"}

    assert client.post("/live-sessions", json=body).status_code == 401
    assert client.post("/live-sessions", json=body, headers=alum).status_code == 403
    assert client.post("/live-sessions", json=body, headers=otro_inst).status_code == 403
    assert client.post("/live-sessions", json={**body, "duration_minutes": 0},
                       headers=inst).status_code == 422
    assert client.post("/live-sessions", json={**body, "course_id": "nope"},
                       headers=inst).status_code == 404

    sid = client.post("/live-sessions", json=body, headers=inst).json()["id"]
    assert client.post(f"/live-sessions/{sid}/start", headers=alum).status_code == 403
    assert client.post(f"/live-sessions/{sid}/start", headers=otro_inst).status_code == 403
    assert client.post("/live-sessions/nope/start", headers=inst).status_code == 404
    assert client.get(f"/live-sessions/{sid}", headers=intruso).status_code == 403
    assert client.get(f"/courses/{cid}/live-sessions", headers=intruso).status_code == 403
    assert client.get(f"/courses/{cid}/live-sessions").status_code == 401

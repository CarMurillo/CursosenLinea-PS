"""Pruebas del patrón Observer (Fase 2): bus de eventos y observadores."""

import logging
from dataclasses import FrozenInstanceError

import pytest

from app.main import app
from app.modules.auth.application.dtos import UserRegisterDTO
from app.modules.auth.application.use_cases import RegisterUserUseCase
from app.modules.auth.domain.models import Role
from app.modules.certificates.application.observers import CertificateIssuerObserver
from app.modules.certificates.infrastructure.stub import InMemoryCertificateIssuer
from app.modules.courses.application.course_facade import CourseFacade
from app.modules.courses.application.dtos import CourseCreateDTO
from app.modules.courses.application.observers import AutoEnrollOnPaymentObserver
from app.modules.courses.application.use_cases import EnrollStudentUseCase
from app.modules.courses.domain.observer import (
    AuditLogObserver,
    EmailNotificationObserver,
    LoggingObserver,
)
from app.modules.courses.infrastructure.repository import InMemoryCourseRepository
from app.modules.notifications.application.observers import InAppNotificationObserver
from app.modules.notifications.infrastructure.repository import (
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
)
from app.modules.payments.application.dtos import PaymentRequestDTO
from app.modules.payments.application.use_cases import (
    AmountBelowPriceError,
    ProcessPaymentUseCase,
)
from app.modules.payments.infrastructure.repository import InMemoryPaymentRepository
from app.modules.recommendations.application.observers import (
    RecommendationProfileObserver,
)
from app.modules.recommendations.infrastructure.repository import (
    InMemoryLearningProfileRepository,
)
from app.shared.domain.events import DomainEvent, EventType, Observer, Subject
from app.shared.infrastructure import container
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository

PWD = "Secreta123"


class Recorder(Observer):
    def __init__(self):
        self.events = []

    def update(self, event):
        self.events.append(event)


class Boom(Observer):
    def update(self, event):
        raise RuntimeError("fallo simulado")


def _event(event_type=EventType.STUDENT_ENROLLED, **kw):
    return DomainEvent(event_type, user_id=kw.pop("user_id", "u1"),
                       course_id=kw.pop("course_id", "c1"), **kw)


# ============================================================ núcleo Subject

def test_domain_event_inmutable():
    event = _event(payload={"a": 1})
    with pytest.raises(FrozenInstanceError):
        event.user_id = "otro"
    with pytest.raises(TypeError):
        event.payload["a"] = 2
    assert event.to_dict()["event_type"] == "student_enrolled"


def test_attach_detach_y_difusion():
    bus, a, b = Subject(), Recorder(), Recorder()
    bus.attach(a)
    bus.attach(b)
    bus.attach(a)  # re-adjuntar no duplica
    bus.notify(_event())
    assert len(a.events) == 1 and len(b.events) == 1
    bus.detach(a)
    bus.notify(_event())
    assert len(a.events) == 1 and len(b.events) == 2
    assert not bus.is_attached(a)


def test_filtro_por_tipo_de_evento():
    bus, pagos, todos = Subject(), Recorder(), Recorder()
    bus.attach(pagos, [EventType.PAYMENT_APPROVED])
    bus.attach(todos)
    bus.notify(_event(EventType.STUDENT_ENROLLED))
    bus.notify(_event(EventType.PAYMENT_APPROVED))
    assert [e.event_type for e in pagos.events] == [EventType.PAYMENT_APPROVED]
    assert len(todos.events) == 2


def test_observador_que_falla_no_detiene_a_los_demas(caplog):
    bus, after = Subject(), Recorder()
    bus.attach(Boom())
    bus.attach(after)
    with caplog.at_level(logging.ERROR):
        bus.notify(_event())  # no propaga la excepción
    assert len(after.events) == 1
    assert "Boom" in caplog.text


def test_encadenado_sin_bucle_infinito():
    """Un observador que re-publica su propio tipo de evento no se dispara a
    sí mismo indefinidamente (guarda de reentrada)."""
    bus = Subject()

    class Echo(Observer):
        calls = 0

        def update(self, event):
            Echo.calls += 1
            bus.notify(_event(event.event_type))

    bus.attach(Echo())
    bus.notify(_event())
    assert Echo.calls == 1


def test_ping_pong_limitado_por_profundidad():
    bus = Subject(max_depth=4)
    seen = Recorder()

    class Ping(Observer):
        def update(self, event):
            bus.notify(_event(EventType.LESSON_COMPLETED))

    class Pong(Observer):
        def update(self, event):
            bus.notify(_event(EventType.ASSESSMENT_SUBMITTED))

    bus.attach(Ping(), [EventType.ASSESSMENT_SUBMITTED])
    bus.attach(Pong(), [EventType.LESSON_COMPLETED])
    bus.attach(seen)
    bus.notify(_event(EventType.ASSESSMENT_SUBMITTED))
    # Se corta: nunca más eventos que la profundidad máxima.
    assert 1 <= len(seen.events) <= 4


def test_encadenado_legitimo_pago_a_inscripcion():
    """PAYMENT_APPROVED -> AutoEnroll -> STUDENT_ENROLLED llega a los demás."""
    courses, payments = InMemoryCourseRepository(), InMemoryPaymentRepository()
    bus, seen = Subject(), Recorder()
    enroll = EnrollStudentUseCase(courses, payment_checker=payments, event_bus=bus)
    bus.attach(AutoEnrollOnPaymentObserver(enroll.execute), [EventType.PAYMENT_APPROVED])
    bus.attach(seen)

    course = CourseFacade(courses).create_course(
        CourseCreateDTO(title="Py", instructor="I", price=20, course_type="video"))
    uc = ProcessPaymentUseCase(payments, event_bus=bus,
                               price_lookup=lambda cid: courses.get_by_id(cid).price)
    uc.execute(PaymentRequestDTO(amount=20, currency="USD", gateway="stripe",
                                 course_id=course.course_id),
               user_id="u1", customer_email="u1@x.com", customer_name="Ana")

    assert course.enrolled_students == ["u1"]
    assert [e.event_type for e in seen.events] == [
        EventType.STUDENT_ENROLLED, EventType.PAYMENT_APPROVED]
    # Idempotente: un PAYMENT_APPROVED repetido no falla ni duplica.
    bus.notify(_event(EventType.PAYMENT_APPROVED, course_id=course.course_id))
    assert course.enrolled_students == ["u1"]


def test_monto_menor_que_precio_rechazado():
    payments = InMemoryPaymentRepository()
    uc = ProcessPaymentUseCase(payments, price_lookup=lambda cid: 100.0)
    with pytest.raises(AmountBelowPriceError):
        uc.execute(PaymentRequestDTO(amount=99, currency="USD", gateway="stripe",
                                     course_id="c1"), user_id="u1", customer_email="x")
    assert payments.list_by_user("u1") == []


# ===================================================== observadores concretos

def test_logging_observer_es_alias_y_log_consultable():
    assert LoggingObserver is AuditLogObserver
    repo = InMemoryAuditLogRepository()
    bus = Subject()
    bus.attach(AuditLogObserver(repo))
    bus.notify(_event(EventType.COURSE_PUBLISHED))
    bus.notify(_event(EventType.STUDENT_ENROLLED))
    assert [e.event_type for e in repo.list_entries()] == ["student_enrolled", "course_published"]
    assert len(repo.list_entries(event_type="course_published")) == 1


def test_email_observer_imprime_y_registra(capsys):
    email = EmailNotificationObserver()
    email.update(_event(payload={"student_name": "Luis Perez", "course_title": "BD"}))
    email.update(_event(EventType.LESSON_COMPLETED))  # sin plantilla: ignora
    assert "Enviando correo a Luis Perez" in capsys.readouterr().out
    assert len(email.sent) == 1


def test_certificado_tras_nota_aprobatoria():
    bus, seen = Subject(), Recorder()
    issuer = InMemoryCertificateIssuer()
    bus.attach(CertificateIssuerObserver(issuer, publisher=bus),
               [EventType.ASSESSMENT_GRADED])
    bus.attach(seen, [EventType.CERTIFICATE_ISSUED])

    bus.notify(_event(EventType.ASSESSMENT_GRADED, payload={"score": 40, "passed": False}))
    assert seen.events == []
    graded = {"score": 90, "passed": True, "assessment_id": "a1"}
    bus.notify(_event(EventType.ASSESSMENT_GRADED, payload=graded))
    bus.notify(_event(EventType.ASSESSMENT_GRADED, payload=graded))  # idempotente
    assert len(seen.events) == 1
    cert = seen.events[0]
    assert cert.user_id == "u1" and cert.course_id == "c1"
    assert cert.payload["certificate_id"] == issuer.list_by_user("u1")[0]["certificate_id"]


def test_in_app_por_usuario_y_eventos_de_curso():
    repo = InMemoryNotificationRepository()
    obs = InAppNotificationObserver(repo, course_members=lambda cid: ["u2", "u3"])
    obs.update(_event(payload={"course_title": "Py"}))
    obs.update(DomainEvent(EventType.LIVE_SESSION_RECORDED, user_id="inst", course_id="c1",
                           payload={"session_title": "Clase 1"}))
    assert [n.event_type for n in repo.list_by_user("u1")] == ["student_enrolled"]
    assert len(repo.list_by_user("u2")) == 1 and len(repo.list_by_user("inst")) == 1
    assert repo.list_by_user("nadie") == []


def test_recommendation_profile_observer():
    profiles = InMemoryLearningProfileRepository()
    obs = RecommendationProfileObserver(profiles)
    obs.update(_event(EventType.STUDENT_ENROLLED))
    obs.update(_event(EventType.LESSON_COMPLETED, payload={"lesson_id": "l1"}))
    obs.update(_event(EventType.ASSESSMENT_GRADED, payload={"score": 80, "passed": True}))
    profile = profiles.get_profile("u1")
    assert profile["enrolled_courses"] == ["c1"]
    assert profile["completed_lessons"] == {"c1": ["l1"]}
    assert profile["assessments"][0]["passed"] is True


def test_build_event_bus_cablea_observadores():
    bus = container.build_event_bus()
    kinds = {type(o) for o in bus.observers}
    assert {AuditLogObserver, EmailNotificationObserver, InAppNotificationObserver,
            AutoEnrollOnPaymentObserver, CertificateIssuerObserver,
            RecommendationProfileObserver} <= kinds
    assert bus is not container.event_bus  # la app usa una sola instancia


# =================================================================== API

def _login(client, email, role, first="Ana", last="Perez"):
    client.post("/auth/register", json={"first_name": first, "last_name": last,
        "email": email, "password": PWD, "role": role})
    r = client.post("/auth/login", json={"email": email, "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _admin(client):
    db = next(app.dependency_overrides[get_db]())
    RegisterUserUseCase(SqlAlchemyUserRepository(db)).execute(UserRegisterDTO(
        first_name="Ad", last_name="Min", email="admin@x.com", password=PWD, role=Role.ADMIN))
    r = client.post("/auth/login", json={"email": "admin@x.com", "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _paid_course(client, inst, price=30):
    # Premium aplica recargo del 20 %: precio final 36 con price=30.
    r = client.post("/courses/", json={"title": "Premium Py", "price": price,
                                       "course_type": "video", "premium": True}, headers=inst)
    assert r.status_code == 201
    return r.json()["id"]


def test_api_pago_inscribe_automaticamente(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student", "Luis", "Perez")
    cid = _paid_course(client, inst)
    r = client.post("/payments/process", json={"amount": 36, "currency": "USD",
        "gateway": "stripe", "course_id": cid}, headers=alum)
    assert r.status_code == 200
    enrolled = client.get("/courses/me/enrolled", headers=alum).json()
    assert [c["id"] for c in enrolled] == [cid]
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 409
    assert client.get(f"/courses/{cid}/content", headers=alum).status_code == 200


def test_api_pago_monto_insuficiente_400(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    cid = _paid_course(client, inst, price=30)
    r = client.post("/payments/process", json={"amount": 35.99, "currency": "USD",
        "gateway": "stripe", "course_id": cid}, headers=alum)
    assert r.status_code == 400
    assert client.get("/courses/me/enrolled", headers=alum).json() == []
    assert client.get("/payments/me", headers=alum).json() == []


def test_api_notificaciones_in_app_por_usuario(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    otro = _login(client, "o@x.com", "student")
    assert client.get("/notifications/me").status_code == 401
    cid = _paid_course(client, inst)
    client.post("/payments/process", json={"amount": 36, "currency": "USD",
        "gateway": "wompi", "course_id": cid}, headers=alum)

    mine = client.get("/notifications/me", headers=alum).json()
    assert {n["event_type"] for n in mine} == {"payment_approved", "student_enrolled"}
    assert all(n["course_id"] == cid for n in mine)
    inst_types = [n["event_type"] for n in client.get("/notifications/me", headers=inst).json()]
    assert inst_types == ["course_published"]
    assert client.get("/notifications/me", headers=otro).json() == []


def test_api_audit_log_401_403_200(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    admin = _admin(client)
    cid = _paid_course(client, inst)
    client.post("/payments/process", json={"amount": 36, "currency": "USD",
        "gateway": "stripe", "course_id": cid}, headers=alum)

    assert client.get("/admin/audit-log").status_code == 401
    assert client.get("/admin/audit-log", headers=alum).status_code == 403
    assert client.get("/admin/audit-log", headers=inst).status_code == 403
    r = client.get("/admin/audit-log", headers=admin)
    assert r.status_code == 200
    types = [e["event_type"] for e in r.json()]
    assert set(types) == {"course_published", "payment_approved", "student_enrolled"}
    filtered = client.get("/admin/audit-log?event_type=payment_approved", headers=admin).json()
    assert len(filtered) == 1 and filtered[0]["course_id"] == cid
    assert client.get("/admin/audit-log?event_type=xx", headers=admin).status_code == 422


def test_api_enroll_gratis_publica_student_enrolled(client, capsys):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student", "Luis", "Perez")
    cid = client.post("/courses/", json={"title": "Gratis", "price": 0,
                                         "course_type": "video"}, headers=inst).json()["id"]
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 200
    assert "Enviando correo a Luis Perez" in capsys.readouterr().out
    entries = container.audit_log_repository.list_entries(event_type="student_enrolled")
    assert len(entries) == 1 and entries[0].payload["student_name"] == "Luis Perez"

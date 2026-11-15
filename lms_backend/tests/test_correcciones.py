"""Pruebas de las correcciones de la Fase 1 (B1-B9 + extras del auditor)."""

import importlib

import pytest

from app.main import app
from app.modules.auth.application.dtos import UserRegisterDTO
from app.modules.auth.application.use_cases import RegisterUserUseCase
from app.modules.auth.domain.models import Role
from app.modules.courses.application.course_facade import CourseFacade
from app.modules.courses.application.dtos import CourseCreateDTO
from app.modules.courses.application.use_cases import (
    AlreadyEnrolledError,
    PaymentRequiredError,
)
from app.modules.courses.domain.bridge import (
    InteractiveQuizLesson,
    VideoLesson,
    VimeoStorageProvider,
)
from app.modules.courses.domain.content_flyweight import ContentMetadataFactory
from app.modules.courses.domain.content_proxy import EnrolledStudentPolicy
from app.modules.courses.infrastructure.repository import InMemoryCourseRepository
from app.modules.payments.application.dtos import PaymentRequestDTO
from app.modules.payments.application.use_cases import (
    PaymentRejectedError,
    ProcessPaymentUseCase,
)
from app.modules.payments.domain.adapter import PaymentGatewayPort, PaymentResult
from app.modules.payments.domain.models import PaymentStatus
from app.modules.payments.infrastructure.api import get_process_payment_use_case
from app.modules.payments.infrastructure.repository import (
    InMemoryPaymentRepository,
    payment_repository,
)
from app.shared.infrastructure.config.system_config import SystemConfig
from app.shared.infrastructure.database import engine, get_db

PWD = "Secreta123"


# ------------------------------------------------------------------ helpers

def _login(client, email, role, first="Ana", last="Perez"):
    client.post("/auth/register", json={"first_name": first, "last_name": last,
        "email": email, "password": PWD, "role": role})
    r = client.post("/auth/login", json={"email": email, "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _admin(client, email="admin@x.com"):
    """El admin no se puede registrar por la API pública: se crea directo."""
    db = next(app.dependency_overrides[get_db]())
    RegisterUserUseCase(_repo(db)).execute(UserRegisterDTO(
        first_name="Ad", last_name="Min", email=email, password=PWD, role=Role.ADMIN))
    r = client.post("/auth/login", json={"email": email, "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _repo(db):
    from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository
    return SqlAlchemyUserRepository(db)


def _course(client, headers, **overrides):
    body = {"title": "Py", "price": 0, "course_type": "video"}
    body.update(overrides)
    r = client.post("/courses/", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _pay(client, headers, course_id, **overrides):
    body = {"amount": 50, "currency": "USD", "gateway": "stripe", "course_id": course_id}
    body.update(overrides)
    return client.post("/payments/process", json=body, headers=headers)


class _RejectingGateway(PaymentGatewayPort):
    def process_payment(self, amount, currency, customer_email):
        return PaymentResult(False, "tx_fail", amount, currency, "Tarjeta rechazada.")


# ------------------------------------------------------------- B1: pagos

def test_b1_services_roto_eliminado():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.modules.payments.domain.services")


def test_b1_use_case_elige_adaptador_por_diccionario():
    repo = InMemoryPaymentRepository()
    uc = ProcessPaymentUseCase(repo)
    for gateway in ("stripe", "wompi"):
        dto = PaymentRequestDTO(amount=10, currency="cop", gateway=gateway, course_id=f"c-{gateway}")
        payment = uc.execute(dto, user_id="u1", customer_email="u1@x.com")
        assert payment.status == PaymentStatus.APPROVED
        assert payment.currency == "COP"
    assert repo.has_approved_payment("u1", "c-stripe")
    assert not repo.has_approved_payment("u2", "c-stripe")


def test_b1_pago_rechazado_se_registra_y_lanza_error():
    repo = InMemoryPaymentRepository()
    uc = ProcessPaymentUseCase(repo, gateways={"stripe": _RejectingGateway()})
    dto = PaymentRequestDTO(amount=10, currency="USD", gateway="stripe", course_id="c1")
    with pytest.raises(PaymentRejectedError):
        uc.execute(dto, user_id="u1", customer_email="u1@x.com")
    assert repo.list_by_user("u1")[0].status == PaymentStatus.REJECTED
    assert not repo.has_approved_payment("u1", "c1")


@pytest.mark.parametrize("gateway", ["stripe", "wompi"])
def test_b1_endpoint_pago_200(client, gateway):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    cid = _course(client, inst, price=50)["id"]
    r = _pay(client, alum, cid, gateway=gateway)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True and body["status"] == "approved"
    assert body["course_id"] == cid
    mine = client.get("/payments/me", headers=alum).json()
    assert [p["payment_id"] for p in mine] == [body["payment_id"]]


@pytest.mark.parametrize("override", [
    {"amount": 0}, {"amount": -5}, {"gateway": "paypal"}, {"currency": "US"},
    {"currency": "U$D"}, {"course_id": ""},
])
def test_b1_endpoint_pago_422(client, override):
    alum = _login(client, "a@x.com", "student")
    body = {"amount": 50, "currency": "USD", "gateway": "stripe", "course_id": "c1", **override}
    assert client.post("/payments/process", json=body, headers=alum).status_code == 422


def test_b1_endpoint_pago_400_rechazado(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    cid = _course(client, inst, price=50)["id"]
    app.dependency_overrides[get_process_payment_use_case] = lambda: ProcessPaymentUseCase(
        payment_repository, gateways={"stripe": _RejectingGateway()})
    r = _pay(client, alum, cid)
    assert r.status_code == 400
    assert "rechazada" in r.json()["detail"]
    # El pago rechazado no habilita la inscripción.
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 403


def test_b1_endpoint_pago_401_404_409(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    cid = _course(client, inst, price=50)["id"]
    assert client.post("/payments/process", json={"amount": 5, "currency": "USD",
        "gateway": "stripe", "course_id": cid}).status_code == 401
    assert _pay(client, alum, "no-existe").status_code == 404
    assert _pay(client, alum, cid).status_code == 200
    assert _pay(client, alum, cid).status_code == 409


# ------------------------------------------- B2/B3: inscripción segura

def test_b2_premium_sin_pago_403_y_no_inscribe(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    cid = _course(client, inst, price=10, premium=True)["id"]
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 403
    assert client.get("/courses/me/enrolled", headers=alum).json() == []
    assert client.get(f"/courses/{cid}/content", headers=alum).status_code == 403


def test_b2_enroll_sin_token_401(client):
    inst = _login(client, "i@x.com", "instructor")
    cid = _course(client, inst)["id"]
    assert client.post(f"/courses/{cid}/enroll", json={"student_name": "X"}).status_code == 401


def test_b2_enroll_guarda_user_id_e_ignora_student_name(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    cid = _course(client, inst)["id"]
    r = client.post(f"/courses/{cid}/enroll", json={"student_name": "Otro"}, headers=alum)
    assert r.status_code == 200
    from app.modules.courses.infrastructure.repository import course_repository
    me = client.post("/auth/login", json={"email": "a@x.com", "password": PWD}).json()["user"]
    assert course_repository.get_by_id(cid).enrolled_students == [me["user_id"]]


def test_b3_inscripcion_duplicada_409(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    cid = _course(client, inst)["id"]
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 200
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 409


def test_b3_use_case_duplicado_y_pago_requerido():
    facade = CourseFacade(InMemoryCourseRepository())
    free = facade.create_course(CourseCreateDTO(title="A", instructor="I", price=0, course_type="video"))
    paid = facade.create_course(CourseCreateDTO(title="B", instructor="I", price=5, course_type="video"))
    facade.enroll_student(free.course_id, "u1")
    with pytest.raises(AlreadyEnrolledError):
        facade.enroll_student(free.course_id, "u1")
    # Sin verificador de pagos inyectado: seguro por defecto, se rechaza.
    with pytest.raises(PaymentRequiredError):
        facade.enroll_student(paid.course_id, "u1")


def test_b2_policy_compara_por_user_id_no_por_nombre():
    facade = CourseFacade(InMemoryCourseRepository())
    course = facade.create_course(CourseCreateDTO(title="A", instructor="I", price=0, course_type="video"))
    facade.enroll_student(course.course_id, "id-ana-1", "Ana Perez")
    policy = EnrolledStudentPolicy()
    assert policy.can_access("id-ana-1", course)
    assert not policy.can_access("id-ana-2", course)       # homónimo, otro id
    assert not policy.can_access("Ana Perez", course)


def test_me_enrolled_lista_solo_inscritos(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    c1 = _course(client, inst, title="Uno")["id"]
    _course(client, inst, title="Dos")
    client.post(f"/courses/{c1}/enroll", headers=alum)
    r = client.get("/courses/me/enrolled", headers=alum)
    assert r.status_code == 200
    assert [c["id"] for c in r.json()] == [c1]
    assert client.get("/courses/me/enrolled").status_code == 401


def test_rutas_literales_no_colisionan(client):
    assert client.get("/courses/content-metadata/video").json()["icon"] == "play-circle"
    assert client.get("/courses/content-metadata/xyz").status_code == 400


def test_pago_luego_inscripcion_y_contenido(client):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    cid = _course(client, inst, price=10, premium=True)["id"]
    assert _pay(client, alum, cid, gateway="wompi", currency="COP").status_code == 200
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 200
    assert client.get(f"/courses/{cid}/content", headers=alum).status_code == 200


# ---------------------------------------------- B4/E1/E2/E3: autorización

def test_b4_crear_curso_401_y_403(client):
    alum = _login(client, "a@x.com", "student")
    body = {"title": "Py", "price": 0, "course_type": "video"}
    assert client.post("/courses/", json=body).status_code == 401
    assert client.post("/courses/", json=body, headers={"Authorization": "Bearer malo"}).status_code == 401
    assert client.post("/courses/", json=body, headers=alum).status_code == 403


def test_e3_instructor_sale_del_token(client):
    inst = _login(client, "i@x.com", "instructor", "Carlos", "Murillo")
    course = _course(client, inst, instructor="Suplantador")
    assert course["instructor"] == "Carlos Murillo"
    me = client.post("/auth/login", json={"email": "i@x.com", "password": PWD}).json()["user"]
    assert course["instructor_id"] == me["user_id"]


def test_b4_e3_clone_y_lessons_exigen_dueno(client):
    owner = _login(client, "i@x.com", "instructor")
    other = _login(client, "o@x.com", "instructor", "Otro", "Inst")
    alum = _login(client, "a@x.com", "student")
    admin = _admin(client)
    cid = _course(client, owner)["id"]
    lesson = {"module_title": "M", "title": "L", "media_id": "1", "provider": "vimeo"}
    for headers, expected in ((None, 401), (alum, 403), (other, 403)):
        assert client.post(f"/courses/{cid}/clone", json={}, headers=headers).status_code == expected
        assert client.post(f"/courses/{cid}/content/lessons", json=lesson,
                           headers=headers).status_code == expected
    assert client.post(f"/courses/{cid}/clone", json={}, headers=admin).status_code == 201
    assert client.post(f"/courses/{cid}/content/lessons", json=lesson, headers=admin).status_code == 201
    assert client.post(f"/courses/no-existe/clone", json={}, headers=owner).status_code == 404


def test_e1_registro_publico_no_permite_admin(client):
    r = client.post("/auth/register", json={"first_name": "A", "last_name": "B",
        "email": "x@x.com", "password": PWD, "role": "admin"})
    assert r.status_code == 403


def test_e2_listar_usuarios_solo_admin(client):
    alum = _login(client, "a@x.com", "student")
    admin = _admin(client)
    assert client.get("/users/").status_code == 401
    assert client.get("/users/", headers=alum).status_code == 403
    r = client.get("/users/", headers=admin)
    assert r.status_code == 200 and len(r.json()) == 2


def test_courses_api_reexporta_get_current_user():
    from app.modules.courses.infrastructure.api import get_current_user as from_courses
    from app.shared.infrastructure.auth_deps import get_current_user
    assert from_courses is get_current_user


# ------------------------------------------------------ B5: Singleton en BD

def test_b5_bd_usa_system_config():
    assert str(engine.url) == SystemConfig().database_url
    # conftest fija DATABASE_URL: pytest no escribe en ./app.db.
    assert SystemConfig().database_url == "sqlite:///:memory:"


# ------------------------------------------------------ B6: bus único

def test_b6_notificador_unico_inyectado():
    from app.modules.courses.infrastructure import api as courses_api
    from app.shared.infrastructure.event_bus import enrollment_notifier
    assert courses_api.facade._notifier is enrollment_notifier


# --------------------------------------------- B7/E6: Prototype + Flyweight

def test_b7_clone_renombra_raiz_composite(client):
    inst = _login(client, "i@x.com", "instructor")
    cid = _course(client, inst, title="Original")["id"]
    from app.modules.courses.infrastructure.repository import course_repository
    r = client.post(f"/courses/{cid}/clone", json={"new_title": "Grupo 2"}, headers=inst)
    clone = course_repository.get_by_id(r.json()["id"])
    assert clone.content.title == "Contenido de Grupo 2"
    assert course_repository.get_by_id(cid).content.title == "Contenido de Original"


def test_b7_clone_decorado_conserva_decoradores_e_id_nuevo():
    facade = CourseFacade(InMemoryCourseRepository())
    course = facade.create_course(CourseCreateDTO(
        title="Py", instructor="I", price=10, course_type="video", premium=True, certificate=True))
    clone = facade.clone_course(course.course_id)
    assert clone.course_id != course.course_id
    assert clone.get_details()["decorators"] == ["premium", "certificate"]
    assert clone.title == "Py (Copia)"


def test_e6_flyweight_compartido_tras_clone():
    facade = CourseFacade(InMemoryCourseRepository())
    course = facade.create_course(CourseCreateDTO(title="Py", instructor="I", price=0, course_type="video"))
    course.content.add_lesson("M", VideoLesson("L", "1", VimeoStorageProvider()))
    clone = facade.clone_course(course.course_id)
    assert clone.content is not course.content
    shared = ContentMetadataFactory.get_metadata("video")
    original_obj = course.content._children[0]._children[0]
    cloned_obj = clone.content._children[0]._children[0]
    assert cloned_obj is not original_obj
    assert original_obj.metadata is shared and cloned_obj.metadata is shared


# ------------------------------------------------------ B8: lecciones

def test_b8_leccion_tiene_id_y_duracion():
    p = VimeoStorageProvider()
    a = VideoLesson("L1", "1", p)
    b = InteractiveQuizLesson("Q", "2", p, duration_minutes=25)
    assert a.duration_minutes == 10 and b.duration_minutes == 25
    assert a.lesson_id and a.lesson_id != b.lesson_id
    assert a.to_dict()["lesson_id"] == a.lesson_id
    assert b.to_dict()["duration_minutes"] == 25
    assert VideoLesson("L", "1", p, lesson_id="fijo").lesson_id == "fijo"


def test_b8_endpoint_lessons_con_duracion(client):
    inst = _login(client, "i@x.com", "instructor")
    cid = _course(client, inst)["id"]
    base = {"module_title": "M", "title": "L", "media_id": "1", "provider": "s3"}
    r = client.post(f"/courses/{cid}/content/lessons", json={**base, "duration_minutes": 30}, headers=inst)
    assert r.status_code == 201
    item = r.json()["content"]["items"][0]["items"][0]
    assert item["duration_minutes"] == 30 and item["lesson_id"] == r.json()["lesson_id"]
    r = client.post(f"/courses/{cid}/content/lessons", json={**base, "lesson_type": "quiz"}, headers=inst)
    assert r.json()["content"]["items"][0]["items"][1]["duration_minutes"] == 10
    assert client.post(f"/courses/{cid}/content/lessons", json={**base, "duration_minutes": 0},
                       headers=inst).status_code == 422

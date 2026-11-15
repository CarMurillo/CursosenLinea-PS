"""
Fase 6: pruebas de regresión de las correcciones de QA que no cubren ya
`test_qa_defectos.py` / `test_qa_criterios.py`.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.modules.payments.application.dtos import PaymentRequestDTO
from app.modules.payments.application.use_cases import (
    AlreadyEnrolledError,
    PaymentNotAllowedError,
    ProcessPaymentUseCase,
)
from app.modules.payments.domain.adapter import (
    StripePaymentAdapter,
    WompiPaymentAdapter,
)
from app.modules.payments.domain.ports import (
    CoursePurchaseInfo,
    CoursePurchaseReaderPort,
)
from app.modules.payments.infrastructure.repository import InMemoryPaymentRepository
from app.main import app
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.models import UserModel

PWD = "Secreta123"
JSON = {"Content-Type": "application/json"}


def _register(client, email, role="student", password=PWD):
    return client.post("/auth/register", json={
        "first_name": "Ana", "last_name": "Perez", "email": email,
        "password": password, "role": role})


def _login(client, email, role="student"):
    assert _register(client, email, role).status_code == 201
    r = client.post("/auth/login", json={"email": email, "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _course(client, headers, **extra):
    body = {"title": "C", "price": 10, "course_type": "video", **extra}
    r = client.post("/courses/", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


# --------------------------------------------------------------------- QA-1

@pytest.mark.parametrize("raw", ["NaN", "Infinity", "-Infinity", "1e999"])
def test_qa1_precio_no_finito_responde_422_serializable(client, raw):
    inst = _login(client, "i@qa.com", "instructor")
    r = client.post("/courses/", headers={**inst, **JSON},
                    content='{"title": "t", "price": %s, "course_type": "video"}' % raw)
    assert r.status_code == 422
    assert r.json()["detail"]  # el cuerpo de error es JSON válido


def test_qa1_topes_de_precio_y_monto():
    with pytest.raises(ValueError):
        PaymentRequestDTO(amount=1_000_000_001, currency="USD",
                          gateway="stripe", course_id="c")
    assert PaymentRequestDTO(amount=1_000_000_000, currency="USD",
                             gateway="stripe", course_id="c").amount == 1e9


def test_qa1_precio_sobre_el_tope_responde_422(client):
    inst = _login(client, "i@qa.com", "instructor")
    r = client.post("/courses/", json={"title": "t", "price": 1e10,
                    "course_type": "video"}, headers=inst)
    assert r.status_code == 422


# --------------------------------------------------------------------- QA-2

def test_qa2_premium_con_precio_cero_responde_422(client):
    inst = _login(client, "i@qa.com", "instructor")
    r = client.post("/courses/", json={"title": "P", "price": 0,
                    "course_type": "video", "premium": True}, headers=inst)
    assert r.status_code == 422
    assert client.post("/courses/", json={"title": "P", "price": 5,
                       "course_type": "video", "premium": True},
                       headers=inst).status_code == 201


# --------------------------------------------------------------------- QA-3

def test_qa3_pagar_curso_gratuito_sin_inscribirse_responde_400(client):
    inst = _login(client, "i@qa.com", "instructor")
    alum = _login(client, "a@qa.com")
    cid = _course(client, inst, price=0)
    r = client.post("/payments/process", json={
        "amount": 5, "currency": "USD", "gateway": "stripe", "course_id": cid},
        headers=alum)
    assert r.status_code == 400 and "gratuito" in r.json()["detail"]
    assert client.get("/payments/me", headers=alum).json() == []


def test_qa3_dueno_no_puede_pagar_su_propio_curso(client):
    inst = _login(client, "i@qa.com", "instructor")
    cid = _course(client, inst, price=10)
    r = client.post("/payments/process", json={
        "amount": 10, "currency": "USD", "gateway": "wompi", "course_id": cid},
        headers=inst)
    assert r.status_code == 400
    assert client.get("/payments/me", headers=inst).json() == []


def test_qa3_pago_valido_sigue_funcionando(client):
    inst = _login(client, "i@qa.com", "instructor")
    alum = _login(client, "a@qa.com")
    cid = _course(client, inst, price=10)
    r = client.post("/payments/process", json={
        "amount": 10, "currency": "USD", "gateway": "stripe", "course_id": cid},
        headers=alum)
    assert r.status_code == 200 and r.json()["success"] is True
    # La inscripción automática deja al usuario inscrito: un 2.º intento ya no cobra.
    r = client.post("/payments/process", json={
        "amount": 10, "currency": "USD", "gateway": "wompi", "course_id": cid},
        headers=alum)
    assert r.status_code == 409


class _FakeReader(CoursePurchaseReaderPort):
    def __init__(self, info, enrolled=False):
        self._info, self._enrolled = info, enrolled

    def get_purchase_info(self, course_id):
        return self._info

    def is_enrolled(self, user_id, course_id):
        return self._enrolled


def _dto():
    return PaymentRequestDTO(amount=10, currency="USD", gateway="stripe", course_id="c1")


def test_qa3_caso_de_uso_usa_el_puerto_de_lectura():
    paid = CoursePurchaseInfo("c1", owner_id="inst", requires_payment=True, price=10)
    repo = InMemoryPaymentRepository()
    with pytest.raises(AlreadyEnrolledError):
        ProcessPaymentUseCase(repo, course_reader=_FakeReader(paid, enrolled=True)) \
            .execute(_dto(), user_id="u1", customer_email="u@x.com")
    with pytest.raises(PaymentNotAllowedError):
        ProcessPaymentUseCase(repo, course_reader=_FakeReader(paid)) \
            .execute(_dto(), user_id="inst", customer_email="i@x.com")
    free = CoursePurchaseInfo("c1", owner_id="inst", requires_payment=False, price=0)
    with pytest.raises(PaymentNotAllowedError):
        ProcessPaymentUseCase(repo, course_reader=_FakeReader(free)) \
            .execute(_dto(), user_id="u1", customer_email="u@x.com")
    assert repo.list_by_user("u1") == []
    payment = ProcessPaymentUseCase(repo, course_reader=_FakeReader(paid)) \
        .execute(_dto(), user_id="u1", customer_email="u@x.com")
    assert payment.is_approved


# --------------------------------------------------------------------- QA-4

@pytest.mark.parametrize("adapter_cls", [StripePaymentAdapter, WompiPaymentAdapter])
def test_qa4_transaction_id_unico_por_pago(adapter_cls):
    ids = {adapter_cls().process_payment(10.0, "USD", "a@x.com").transaction_id
           for _ in range(5)}
    assert len(ids) == 5


# --------------------------------------------------------------------- QA-5

def test_qa5_password_de_7_caracteres_responde_422(client):
    assert _register(client, "c@qa.com", password="1234567").status_code == 422
    assert _register(client, "c@qa.com", password="12345678").status_code == 201


def test_qa5_correo_se_guarda_en_minusculas_y_login_ignora_mayusculas(client):
    r = _register(client, "  Mixto@QA.com ")
    assert r.status_code == 201 and r.json()["email"] == "mixto@qa.com"
    r = client.post("/auth/login", json={"email": "MIXTO@qa.COM", "password": PWD})
    assert r.status_code == 200


def test_qa5_nombres_solo_espacios_responde_422(client):
    r = client.post("/auth/register", json={
        "first_name": "   ", "last_name": "B", "email": "s@qa.com",
        "password": PWD, "role": "student"})
    assert r.status_code == 422


# --------------------------------------------------------------------- QA-9

def test_qa9_usuario_inactivo_recibe_401(client):
    alum = _login(client, "a@qa.com")
    assert client.get("/payments/me", headers=alum).status_code == 200
    # Misma BD en memoria que usa el cliente (dependencia sobrescrita en conftest).
    sessions = app.dependency_overrides[get_db]()
    db = next(sessions)
    try:
        user = db.query(UserModel).filter(UserModel.email == "a@qa.com").first()
        user.is_active = False
        db.commit()
    finally:
        sessions.close()
    assert client.get("/payments/me", headers=alum).status_code == 401
    r = client.post("/auth/login", json={"email": "a@qa.com", "password": PWD})
    assert r.status_code == 401


# -------------------------------------------------------------------- QA-10

def test_qa10_clase_en_vivo_en_el_pasado_responde_422(client):
    inst = _login(client, "i@qa.com", "instructor")
    cid = _course(client, inst, price=0)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    r = client.post("/live-sessions", json={"course_id": cid, "title": "C",
                    "scheduled_at": past}, headers=inst)
    assert r.status_code == 422
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    r = client.post("/live-sessions", json={"course_id": cid, "title": "C",
                    "scheduled_at": future}, headers=inst)
    assert r.status_code == 201


@pytest.mark.parametrize("options", [["a", ""], ["a", "  "], ["a", "a"], ["Si", "si "]])
def test_qa10_opciones_vacias_o_duplicadas_responden_422(client, options):
    inst = _login(client, "i@qa.com", "instructor")
    cid = _course(client, inst, price=0)
    aid = client.post("/assessments", json={"course_id": cid, "title": "Q"},
                      headers=inst).json()["id"]
    r = client.post(f"/assessments/{aid}/questions", json={
        "text": "t", "options": options, "correct_option": 0}, headers=inst)
    assert r.status_code == 422


def test_qa10_mensaje_de_progreso_en_curso_gratuito_no_inscrito(client):
    inst = _login(client, "i@qa.com", "instructor")
    alum = _login(client, "a@qa.com")
    cid = _course(client, inst, price=0)
    r = client.get(f"/courses/{cid}/progress/me", headers=alum)
    assert r.status_code == 403
    assert r.json()["detail"].startswith("Debes estar inscrito en el curso")
    assert "Premium" not in r.json()["detail"]

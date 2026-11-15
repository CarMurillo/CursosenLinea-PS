"""Pruebas reales del patrón Adapter (pasarelas Stripe/Wompi simuladas) y del
caso de uso de pagos. Reemplaza la antigua demostración por consola
`test_semana7.py` (no tenía asserts; pytest no recolectaba ninguna prueba).

La parte Bridge de esa demo está cubierta en test_courses_patterns.py y
test_visitor.py.
"""

import pytest

from app.modules.payments.application.dtos import PaymentRequestDTO
from app.modules.payments.application.use_cases import (
    AlreadyPaidError,
    AmountBelowPriceError,
    PaymentRejectedError,
    ProcessPaymentUseCase,
    UnsupportedGatewayError,
    default_gateways,
)
from app.modules.payments.domain.adapter import (
    PaymentGatewayPort,
    PaymentResult,
    StripePaymentAdapter,
    StripeSDK,
    WompiPaymentAdapter,
    WompiSDK,
)
from app.modules.payments.domain.models import PaymentStatus
from app.modules.payments.infrastructure.repository import InMemoryPaymentRepository
from app.shared.domain.events import EventType


# ------------------------------------------------------------------ Adapter

def test_stripe_adapter_traduce_a_centavos_y_normaliza_respuesta():
    calls = []

    class SpySDK(StripeSDK):
        def create_charge(self, amount_in_cents, currency_code, email):
            calls.append((amount_in_cents, currency_code, email))
            return super().create_charge(amount_in_cents, currency_code, email)

    result = StripePaymentAdapter(SpySDK()).process_payment(49.99, "USD", "a@x.com")
    assert calls == [(4999, "USD", "a@x.com")]
    assert isinstance(result, PaymentResult)
    assert result.success is True
    # QA-4: el id simulado es único por cargo (uuid), ya no "ch_stripe_<centavos>".
    assert result.transaction_id.startswith("ch_stripe_")
    assert result.transaction_id != StripePaymentAdapter(SpySDK()).process_payment(
        49.99, "USD", "a@x.com").transaction_id
    assert (result.amount, result.currency) == (49.99, "USD")


def test_wompi_adapter_usa_referencia_y_normaliza_respuesta():
    calls = []

    class SpySDK(WompiSDK):
        def create_transaction(self, amount_in_cop, reference, payer_email):
            calls.append((amount_in_cop, reference, payer_email))
            return super().create_transaction(amount_in_cop, reference, payer_email)

    result = WompiPaymentAdapter(SpySDK()).process_payment(150000.0, "COP", "ana@u.edu")
    assert calls == [(150000.0, "REF-LMS-ana", "ana@u.edu")]
    assert result.success is True
    # QA-4: el id simulado es único por transacción (uuid).
    assert result.transaction_id.startswith("wompi_tx_")
    assert result.transaction_id != WompiPaymentAdapter(SpySDK()).process_payment(
        150000.0, "COP", "ana@u.edu").transaction_id
    assert "Wompi" in result.message


@pytest.mark.parametrize("sdk_response, adapter_cls, sdk_cls, method", [
    ({"id": "ch_x", "status": "failed"}, StripePaymentAdapter, StripeSDK, "create_charge"),
    ({"data": {"id": "w_x", "status": "DECLINED"}}, WompiPaymentAdapter, WompiSDK,
     "create_transaction"),
])
def test_adapters_reportan_rechazo_del_sdk(sdk_response, adapter_cls, sdk_cls, method):
    sdk = sdk_cls()
    setattr(sdk, method, lambda *a, **k: sdk_response)
    result = adapter_cls(sdk).process_payment(10.0, "USD", "a@x.com")
    assert result.success is False


def test_ambos_adaptadores_cumplen_el_mismo_puerto():
    gateways = default_gateways()
    assert set(gateways) == {"stripe", "wompi"}
    for adapter in gateways.values():
        assert isinstance(adapter, PaymentGatewayPort)
        assert adapter.process_payment(20.0, "USD", "a@x.com").success is True


# ------------------------------------------------------------------ caso de uso

class _Bus:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)


def _dto(**overrides):
    body = {"amount": 50, "currency": "usd", "gateway": "wompi", "course_id": "c1"}
    body.update(overrides)
    return PaymentRequestDTO(**body)


def test_caso_de_uso_aprueba_guarda_y_publica_payment_approved():
    repo, bus = InMemoryPaymentRepository(), _Bus()
    payment = ProcessPaymentUseCase(repo, event_bus=bus).execute(
        _dto(), user_id="u1", customer_email="a@x.com")
    assert payment.status is PaymentStatus.APPROVED
    assert payment.currency == "USD"
    assert repo.has_approved_payment("u1", "c1")
    assert [e.event_type for e in bus.events] == [EventType.PAYMENT_APPROVED]
    assert bus.events[0].payload["gateway"] == "wompi"


def test_caso_de_uso_duplicado_monto_bajo_y_pasarela_desconocida():
    repo = InMemoryPaymentRepository()
    use_case = ProcessPaymentUseCase(repo, price_lookup=lambda cid: 80.0)
    with pytest.raises(AmountBelowPriceError):
        use_case.execute(_dto(amount=50), user_id="u1", customer_email="a@x.com")
    use_case.execute(_dto(amount=80), user_id="u1", customer_email="a@x.com")
    with pytest.raises(AlreadyPaidError):
        use_case.execute(_dto(amount=80), user_id="u1", customer_email="a@x.com")
    with pytest.raises(UnsupportedGatewayError):
        ProcessPaymentUseCase(repo, gateways={}).execute(
            _dto(), user_id="u2", customer_email="b@x.com")


def test_caso_de_uso_rechazado_no_publica_evento():
    class Rejecting(PaymentGatewayPort):
        def process_payment(self, amount, currency, customer_email):
            return PaymentResult(False, "tx0", amount, currency, "Fondos insuficientes")

    repo, bus = InMemoryPaymentRepository(), _Bus()
    use_case = ProcessPaymentUseCase(repo, gateways={"wompi": Rejecting()}, event_bus=bus)
    with pytest.raises(PaymentRejectedError) as info:
        use_case.execute(_dto(), user_id="u1", customer_email="a@x.com")
    assert info.value.payment.status is PaymentStatus.REJECTED
    assert repo.list_by_user("u1")[0].message == "Fondos insuficientes"
    assert not repo.has_approved_payment("u1", "c1")
    assert bus.events == []


# ------------------------------------------------------------------ endpoint

def _login(client, email, role):
    client.post("/auth/register", json={"first_name": "Ana", "last_name": "Perez",
        "email": email, "password": "Secreta123", "role": role})
    r = client.post("/auth/login", json={"email": email, "password": "Secreta123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_endpoint_pago_wompi_y_historial(client):
    inst = _login(client, "i@x.com", "instructor")
    cid = client.post("/courses/", json={"title": "Pago", "price": 30,
        "course_type": "video"}, headers=inst).json()["id"]
    alum = _login(client, "a@x.com", "student")

    assert client.post("/payments/process", json={"amount": 30, "currency": "COP",
        "gateway": "wompi", "course_id": cid}).status_code == 401
    assert client.post("/payments/process", json={"amount": 30, "currency": "COP",
        "gateway": "paypal", "course_id": cid}, headers=alum).status_code == 422

    r = client.post("/payments/process", json={"amount": 30, "currency": "COP",
        "gateway": "wompi", "course_id": cid}, headers=alum)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "approved"
    assert r.json()["transaction_id"].startswith("wompi_tx_")

    history = client.get("/payments/me", headers=alum).json()
    assert [p["course_id"] for p in history] == [cid]

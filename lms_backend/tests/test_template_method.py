"""Pruebas del patrón Template Method en los adaptadores de pago.

`TemplatePaymentAdapter.process_payment` fija el algoritmo de cobro; las
pasarelas concretas solo implementan los pasos variables.
"""

import pytest

from app.modules.payments.application.use_cases import ProcessPaymentUseCase
from app.modules.payments.domain.adapter import (
    PaymentGatewayPort,
    PaymentResult,
    StripePaymentAdapter,
    StripeSDK,
    TemplatePaymentAdapter,
    WompiPaymentAdapter,
    WompiSDK,
)
from app.main import app
from app.modules.payments.infrastructure.api import get_process_payment_use_case
from app.shared.infrastructure.container import payment_repository


class _FakeGateway(TemplatePaymentAdapter):
    """Pasarela nueva: solo implementa los pasos, no el flujo."""

    gateway_name = "Fake"

    def __init__(self, response=None, error=None):
        self.calls = []
        self._response = response or {"ok": True, "tx": "fake_1"}
        self._error = error

    def _call_gateway(self, amount, currency, customer_email):
        self.calls.append((amount, currency, customer_email))
        if self._error:
            raise self._error
        return self._response

    def _is_approved(self, response):
        return response.get("ok") is True

    def _transaction_id(self, response):
        return response.get("tx", "")


def test_clase_plantilla_es_abstracta():
    with pytest.raises(TypeError):
        TemplatePaymentAdapter()


def test_adaptadores_concretos_heredan_el_metodo_plantilla():
    for cls in (StripePaymentAdapter, WompiPaymentAdapter, _FakeGateway):
        assert issubclass(cls, TemplatePaymentAdapter)
        assert issubclass(cls, PaymentGatewayPort)
        # Nadie sobrescribe el esqueleto.
        assert cls.process_payment is TemplatePaymentAdapter.process_payment


def test_pasarela_nueva_solo_con_pasos_funciona():
    gw = _FakeGateway()
    result = gw.process_payment(25.0, "usd", "a@x.com")
    assert isinstance(result, PaymentResult)
    assert result.success is True
    assert result.transaction_id == "fake_1"
    assert result.currency == "USD"  # paso invariante: moneda en mayúsculas
    assert result.message == "Pago procesado exitosamente vía Fake."
    assert gw.calls == [(25.0, "USD", "a@x.com")]  # gancho por defecto: monto igual


def test_rechazo_usa_mensaje_por_defecto():
    result = _FakeGateway(response={"ok": False}).process_payment(5.0, "USD", "a@x.com")
    assert result.success is False
    assert result.message == "Pago rechazado por Fake."


@pytest.mark.parametrize("amount", [0, -10.0, None, float("nan"), float("inf")])
def test_monto_invalido_no_llama_al_sdk(amount):
    gw = _FakeGateway()
    result = gw.process_payment(amount, "USD", "a@x.com")
    assert result.success is False
    assert gw.calls == []


def test_fallo_del_sdk_se_convierte_en_rechazo():
    gw = _FakeGateway(error=ConnectionError("timeout"))
    result = gw.process_payment(10.0, "USD", "a@x.com")
    assert result.success is False
    assert "no respondió" in result.message
    assert "timeout" not in result.message  # sin detalle interno


def test_gancho_prepare_amount_de_stripe_cobra_en_centavos():
    seen = {}

    class SpySDK(StripeSDK):
        def create_charge(self, amount_in_cents, currency_code, email):
            seen["cents"] = amount_in_cents
            return super().create_charge(amount_in_cents, currency_code, email)

    result = StripePaymentAdapter(SpySDK()).process_payment(19.99, "usd", "a@x.com")
    assert seen["cents"] == 1999
    assert result.amount == 19.99 and result.currency == "USD"



def test_respuesta_malformada_del_sdk_es_rechazo():
    """Un SDK que devuelve None no debe propagar AttributeError (HTTP 500)."""
    class NoneSDK(StripeSDK):
        def create_charge(self, amount_in_cents, currency_code, email):
            return None

    result = StripePaymentAdapter(NoneSDK()).process_payment(10.0, "USD", "a@x.com")
    assert result.success is False
    assert result.transaction_id == ""


# ------------------------------------------------- por API (sin HTTP 500)

class _BrokenStripeSDK(StripeSDK):
    def create_charge(self, amount_in_cents, currency_code, email):
        raise ConnectionError("stripe caído")


class _BrokenWompiSDK(WompiSDK):
    def create_transaction(self, amount_in_cop, reference, payer_email):
        raise TimeoutError("wompi sin respuesta")


def _login(client, email, role):
    client.post("/auth/register", json={"first_name": "Ana", "last_name": "Perez",
        "email": email, "password": "Secreta123", "role": role})
    r = client.post("/auth/login", json={"email": email, "password": "Secreta123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.parametrize("gateway, adapter", [
    ("stripe", lambda: StripePaymentAdapter(_BrokenStripeSDK())),
    ("wompi", lambda: WompiPaymentAdapter(_BrokenWompiSDK())),
])
def test_api_sdk_que_lanza_excepcion_responde_400_no_500(client, gateway, adapter):
    inst = _login(client, "i@x.com", "instructor")
    alum = _login(client, "a@x.com", "student")
    cid = client.post("/courses/", json={"title": "Py", "price": 50,
        "course_type": "video"}, headers=inst).json()["id"]
    app.dependency_overrides[get_process_payment_use_case] = lambda: ProcessPaymentUseCase(
        payment_repository, gateways={gateway: adapter()})

    r = client.post("/payments/process", json={"amount": 50, "currency": "USD",
        "gateway": gateway, "course_id": cid}, headers=alum)

    assert r.status_code == 400, r.text
    assert "no respondió" in r.json()["detail"]
    # Queda registrado como rechazado y no inscribe al estudiante.
    history = client.get("/payments/me", headers=alum).json()
    assert [p["status"] for p in history] == ["rejected"]
    assert client.get("/courses/me/enrolled", headers=alum).json() == []


@pytest.mark.parametrize("amount", [0, -1])
def test_api_monto_no_positivo_lo_rechaza_el_dto_antes_del_sdk(client, amount):
    """El DTO (gt=0) sigue respondiendo 422; el Template Method es una
    segunda barrera de dominio y no cambia ese contrato."""
    alum = _login(client, "a@x.com", "student")
    calls = []

    class SpyGateway(_FakeGateway):
        def _call_gateway(self, *args):
            calls.append(args)
            return super()._call_gateway(*args)

    app.dependency_overrides[get_process_payment_use_case] = lambda: ProcessPaymentUseCase(
        payment_repository, gateways={"stripe": SpyGateway()})
    r = client.post("/payments/process", json={"amount": amount, "currency": "USD",
        "gateway": "stripe", "course_id": "c1"}, headers=alum)
    assert r.status_code == 422
    assert calls == []

"""
Módulo: Payments - Capa de Dominio / Infraestructura
Patrones de Diseño: Adapter (Estructural) + Template Method (Comportamiento)
Principios SOLID: DIP, OCP, LSP, ISP, SRP

Adapter: cada pasarela traduce su SDK al puerto `PaymentGatewayPort`.

Template Method: todas las pasarelas siguen el MISMO algoritmo de cobro
(validar -> preparar petición -> llamar al SDK -> interpretar respuesta ->
construir `PaymentResult`). `TemplatePaymentAdapter.process_payment` fija ese
esqueleto una sola vez; cada adaptador concreto solo implementa los pasos
variables (`_call_gateway`, `_is_approved`, `_transaction_id`) y, si quiere,
los ganchos (`_prepare_amount`, mensajes). Agregar una pasarela = escribir
esos pasos, sin copiar el flujo ni el manejo de errores.
"""

import logging
import math
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any

logger = logging.getLogger(__name__)


# DTO neutro de dominio para abstraer respuestas de transacciones
@dataclass
class PaymentResult:
    success: bool
    transaction_id: str
    amount: float
    currency: str
    message: str


# Target / Port (DIP e ISP): Contrato delgado que define la abstracción requerida por el backend
class PaymentGatewayPort(ABC):
    @abstractmethod
    def process_payment(self, amount: float, currency: str, customer_email: str) -> PaymentResult:
        pass


# --- LIBRERÍAS / SDKs EXTERNOS SIMULADOS (Adaptees) ---

class StripeSDK:
    """Simula el SDK oficial de Stripe."""
    def create_charge(self, amount_in_cents: int, currency_code: str, email: str) -> Dict[str, Any]:
        return {
            # Id simulado único por cargo (antes se repetía con montos iguales).
            "id": f"ch_stripe_{uuid.uuid4().hex}",
            "status": "succeeded",
            "charged_amount": amount_in_cents / 100
        }


class WompiSDK:
    """Simula la API/SDK de Wompi (Pasarela de pagos en Colombia)."""
    def create_transaction(self, amount_in_cop: float, reference: str, payer_email: str) -> Dict[str, Any]:
        return {
            "data": {
                # Id simulado único por transacción.
                "id": f"wompi_tx_{uuid.uuid4().hex}",
                "status": "APPROVED",
                "reference": reference
            }
        }


# --- TEMPLATE METHOD: esqueleto común de cobro ---

class TemplatePaymentAdapter(PaymentGatewayPort):
    """Clase abstracta del patrón Template Method.

    `process_payment` es el método plantilla: define el orden de los pasos y
    las reglas comunes (monto positivo, moneda en mayúsculas, un fallo del SDK
    se convierte en un rechazo en lugar de propagar la excepción). Las
    subclases NO deben sobrescribirlo.
    """

    gateway_name: str = "pasarela"

    def process_payment(self, amount: float, currency: str, customer_email: str) -> PaymentResult:
        # 1. Validación común (invariante).
        # isfinite: NaN no cumple `<= 0` y llegaba al SDK (Stripe fallaba en round()).
        if amount is None or not math.isfinite(amount) or amount <= 0:
            return self._result(False, "", amount, currency,
                                f"Monto inválido para {self.gateway_name}.")
        currency = (currency or "").upper()

        # 2. Preparación del monto (gancho con implementación por defecto).
        gateway_amount = self._prepare_amount(amount)

        # 3. Llamada al SDK y 4. interpretación de la respuesta (pasos
        # abstractos). Un error del SDK o una respuesta malformada (p. ej.
        # None) es un rechazo, no una excepción que llegue como HTTP 500.
        try:
            response = self._call_gateway(gateway_amount, currency, customer_email)
            approved = self._is_approved(response)
            tx_id = self._transaction_id(response)
        except Exception as exc:  # noqa: BLE001 - frontera con un SDK externo
            # El detalle técnico va solo al log: no se expone al cliente.
            logger.warning("Fallo del SDK de %s: %r", self.gateway_name, exc)
            return self._result(False, "", amount, currency,
                                f"{self.gateway_name} no respondió. Intenta de nuevo más tarde.")

        message = self._success_message() if approved else self._failure_message()

        # 5. Construcción del resultado neutro (invariante).
        return self._result(approved, tx_id, amount, currency, message)

    # ---------------------------------------------- pasos abstractos
    @abstractmethod
    def _call_gateway(self, amount: Any, currency: str, customer_email: str) -> Dict[str, Any]:
        """Invoca el SDK concreto y devuelve su respuesta cruda."""

    @abstractmethod
    def _is_approved(self, response: Dict[str, Any]) -> bool:
        """Decide si la respuesta cruda del SDK es un pago aprobado."""

    @abstractmethod
    def _transaction_id(self, response: Dict[str, Any]) -> str:
        """Extrae el id de transacción de la respuesta cruda."""

    # ---------------------------------------------- ganchos (hooks)
    def _prepare_amount(self, amount: float) -> Any:
        return amount

    def _success_message(self) -> str:
        return f"Pago procesado exitosamente vía {self.gateway_name}."

    def _failure_message(self) -> str:
        return f"Pago rechazado por {self.gateway_name}."

    # ---------------------------------------------- operación común
    @staticmethod
    def _result(success: bool, tx_id: str, amount: float, currency: str, message: str) -> PaymentResult:
        return PaymentResult(
            success=success,
            transaction_id=tx_id,
            amount=amount,
            currency=currency,
            message=message,
        )


# --- ADAPTADORES CONCRETOS (Adapters + pasos del Template Method) ---

class StripePaymentAdapter(TemplatePaymentAdapter):
    """Adapter de Stripe: cobra en centavos."""

    gateway_name = "Stripe"

    def __init__(self, stripe_sdk: StripeSDK = None):
        self._sdk = stripe_sdk or StripeSDK()

    def _prepare_amount(self, amount: float) -> int:
        # round() y no int(): 19.99 * 100 = 1998.99... e int() truncaba a 1998.
        return round(amount * 100)

    def _call_gateway(self, amount, currency, customer_email):
        return self._sdk.create_charge(amount, currency, customer_email)

    def _is_approved(self, response):
        return response.get("status") == "succeeded"

    def _transaction_id(self, response):
        return response.get("id", "")

    def _failure_message(self) -> str:
        return "Error en Stripe."


class WompiPaymentAdapter(TemplatePaymentAdapter):
    """Adapter de Wompi (Colombia): opera con referencia y montos en COP.
    Demuestra cómo añadir nuevos medios de pago sin alterar el dominio."""

    gateway_name = "Wompi (Colombia)"

    def __init__(self, wompi_sdk: WompiSDK = None):
        self._sdk = wompi_sdk or WompiSDK()

    def _call_gateway(self, amount, currency, customer_email):
        reference = f"REF-LMS-{customer_email.split('@')[0]}"
        return self._sdk.create_transaction(amount, reference, customer_email)

    def _is_approved(self, response):
        return response.get("data", {}).get("status") == "APPROVED"

    def _transaction_id(self, response):
        return response.get("data", {}).get("id", "")

    def _failure_message(self) -> str:
        return "Rechazado por Wompi."

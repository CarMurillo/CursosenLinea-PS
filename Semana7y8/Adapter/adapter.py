"""
Módulo: Payments - Capa de Dominio / Infraestructura
Patrón de Diseño: Adapter (Estructural)
Principios SOLID: DIP, OCP, LSP, ISP, SRP
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any


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
            "id": f"ch_stripe_{amount_in_cents}",
            "status": "succeeded",
            "charged_amount": amount_in_cents / 100
        }


class WompiSDK:
    """Simula la API/SDK de Wompi (Pasarela de pagos en Colombia)."""
    def create_transaction(self, amount_in_cop: float, reference: str, payer_email: str) -> Dict[str, Any]:
        return {
            "data": {
                "id": f"wompi_tx_{int(amount_in_cop)}",
                "status": "APPROVED",
                "reference": reference
            }
        }


# --- ADAPTADORES CONCRETOS (Adapters) ---

class StripePaymentAdapter(PaymentGatewayPort):
    """
    Adapter para integrar Stripe cumpliendo LSP y OCP.
    """
    def __init__(self, stripe_sdk: StripeSDK = None):
        self._sdk = stripe_sdk or StripeSDK()

    def process_payment(self, amount: float, currency: str, customer_email: str) -> PaymentResult:
        # Traduce los requerimientos del dominio al formato específico de Stripe (centavos)
        amount_cents = int(amount * 100)
        response = self._sdk.create_charge(amount_cents, currency, customer_email)
        
        is_success = response.get("status") == "succeeded"
        return PaymentResult(
            success=is_success,
            transaction_id=response.get("id", ""),
            amount=amount,
            currency=currency,
            message="Pago procesado exitosamente vía Stripe." if is_success else "Error en Stripe."
        )


class WompiPaymentAdapter(PaymentGatewayPort):
    """
    Adapter para pasarela colombiana (Wompi/PSE/Tarjetas COP).
    Demuestra cómo añadir nuevos medios de pago sin alterar el dominio.
    """
    def __init__(self, wompi_sdk: WompiSDK = None):
        self._sdk = wompi_sdk or WompiSDK()

    def process_payment(self, amount: float, currency: str, customer_email: str) -> PaymentResult:
        # Wompi opera habitualmente con referencia y montos en COP
        reference = f"REF-LMS-{customer_email.split('@')[0]}"
        response = self._sdk.create_transaction(amount, reference, customer_email)
        
        tx_data = response.get("data", {})
        is_success = tx_data.get("status") == "APPROVED"
        return PaymentResult(
            success=is_success,
            transaction_id=tx_data.get("id", ""),
            amount=amount,
            currency=currency,
            message="Pago procesado exitosamente vía Wompi (Colombia)." if is_success else "Rechazado por Wompi."
        )
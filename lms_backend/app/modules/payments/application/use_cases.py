"""
Casos de uso del módulo de pagos.

Patrón Adapter: el caso de uso trabaja contra PaymentGatewayPort; la
pasarela concreta (Stripe/Wompi simuladas) se elige con un diccionario,
sin cadenas de if/elif. Agregar una pasarela = agregar una entrada.
"""

from typing import Any, Dict, Optional

from app.modules.payments.application.dtos import PaymentRequestDTO
from app.modules.payments.domain.adapter import (
    StripePaymentAdapter,
    WompiPaymentAdapter,
)
from app.modules.payments.domain.models import Payment, PaymentStatus
from app.modules.payments.domain.ports import PaymentGatewayPort, PaymentRepository


class UnsupportedGatewayError(ValueError):
    pass


class PaymentRejectedError(Exception):
    def __init__(self, payment: Payment):
        super().__init__(payment.message or "Pago rechazado por la pasarela.")
        self.payment = payment


class AlreadyPaidError(Exception):
    pass


def default_gateways() -> Dict[str, PaymentGatewayPort]:
    return {
        "stripe": StripePaymentAdapter(),
        "wompi": WompiPaymentAdapter(),
    }


class ProcessPaymentUseCase:
    """Procesa el pago de un curso y lo registra en el repositorio."""

    def __init__(
        self,
        repository: PaymentRepository,
        gateways: Optional[Dict[str, PaymentGatewayPort]] = None,
        event_bus: Optional[Any] = None,
    ):
        self.repository = repository
        self._gateways = gateways if gateways is not None else default_gateways()
        # Punto de inyección del bus de eventos. La Fase 2 publicará aquí
        # PAYMENT_APPROVED (inscripción automática vía Observer).
        self.event_bus = event_bus

    def execute(
        self,
        dto: PaymentRequestDTO,
        user_id: str,
        customer_email: str,
    ) -> Payment:
        gateway = self._gateways.get(dto.gateway)
        if gateway is None:
            raise UnsupportedGatewayError(f"Pasarela no soportada: {dto.gateway}")

        if self.repository.has_approved_payment(user_id, dto.course_id):
            raise AlreadyPaidError(dto.course_id)

        result = gateway.process_payment(
            amount=dto.amount,
            currency=dto.currency.upper(),
            customer_email=customer_email,
        )

        payment = Payment(
            user_id=user_id,
            course_id=dto.course_id,
            amount=result.amount,
            currency=result.currency,
            gateway=dto.gateway,
            status=PaymentStatus.APPROVED if result.success else PaymentStatus.REJECTED,
            transaction_id=result.transaction_id,
            message=result.message,
        )
        self.repository.save(payment)

        if not payment.is_approved:
            raise PaymentRejectedError(payment)

        return payment

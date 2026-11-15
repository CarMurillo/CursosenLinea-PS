"""
Casos de uso del módulo de pagos.

Patrón Adapter: el caso de uso trabaja contra PaymentGatewayPort; la
pasarela concreta (Stripe/Wompi simuladas) se elige con un diccionario,
sin cadenas de if/elif. Agregar una pasarela = agregar una entrada.

Observer: un pago aprobado publica PAYMENT_APPROVED en el bus inyectado; el
AutoEnrollOnPaymentObserver inscribe automáticamente al estudiante.

Regla de monto: si se inyecta `price_lookup`, el pago se rechaza
(AmountBelowPriceError -> HTTP 400) cuando `amount` < precio del curso.
LIMITACIÓN conocida: no hay conversión de moneda; se compara el número tal
cual, sin importar `currency` (p. ej. 50 COP "cubre" un curso de 10 USD).

Reglas de compra (si se inyecta `course_reader`, puerto
CoursePurchaseReaderPort): no se cobra si el usuario ya está inscrito
(AlreadyEnrolledError -> 409), si es el dueño del curso o si el curso no
requiere pago (PaymentNotAllowedError -> 400).
"""

from typing import Callable, Dict, Optional

from app.modules.payments.application.dtos import PaymentRequestDTO
from app.modules.payments.domain.adapter import (
    StripePaymentAdapter,
    WompiPaymentAdapter,
)
from app.modules.payments.domain.models import Payment, PaymentStatus
from app.modules.payments.domain.ports import (
    CoursePurchaseReaderPort,
    PaymentGatewayPort,
    PaymentRepository,
)
from app.shared.domain.events import (
    DomainEvent,
    EventPublisher,
    EventType,
    publish_event,
)

# Devuelve el precio del curso o None si no existe/no se conoce.
PriceLookup = Callable[[str], Optional[float]]


class UnsupportedGatewayError(ValueError):
    pass


class PaymentRejectedError(Exception):
    def __init__(self, payment: Payment):
        super().__init__(payment.message or "Pago rechazado por la pasarela.")
        self.payment = payment


class AlreadyPaidError(Exception):
    pass


class AmountBelowPriceError(ValueError):
    """El monto pagado es menor que el precio del curso (HTTP 400)."""


class AlreadyEnrolledError(Exception):
    """El usuario ya está inscrito en el curso: no se cobra (HTTP 409)."""


class PaymentNotAllowedError(ValueError):
    """El curso no requiere pago o el usuario es su dueño (HTTP 400)."""


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
        event_bus: Optional[EventPublisher] = None,
        price_lookup: Optional[PriceLookup] = None,
        course_reader: Optional[CoursePurchaseReaderPort] = None,
    ):
        self.repository = repository
        self._course_reader = course_reader
        self._gateways = gateways if gateways is not None else default_gateways()
        self.event_bus = event_bus
        self._price_lookup = price_lookup

    def execute(
        self,
        dto: PaymentRequestDTO,
        user_id: str,
        customer_email: str,
        customer_name: Optional[str] = None,
    ) -> Payment:
        gateway = self._gateways.get(dto.gateway)
        if gateway is None:
            raise UnsupportedGatewayError(f"Pasarela no soportada: {dto.gateway}")

        if self.repository.has_approved_payment(user_id, dto.course_id):
            raise AlreadyPaidError(dto.course_id)

        self._ensure_purchase_allowed(user_id, dto.course_id)

        if self._price_lookup is not None:
            price = self._price_lookup(dto.course_id)
            if price is not None and dto.amount < float(price):
                raise AmountBelowPriceError(
                    f"El monto ({dto.amount}) es menor que el precio del "
                    f"curso ({price})."
                )

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

        publish_event(self.event_bus, DomainEvent(
            EventType.PAYMENT_APPROVED,
            user_id=user_id,
            course_id=payment.course_id,
            payload={
                "payment_id": payment.payment_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "gateway": payment.gateway,
                "transaction_id": payment.transaction_id,
                "customer_email": customer_email,
                "customer_name": customer_name,
            },
        ))

        return payment

    def _ensure_purchase_allowed(self, user_id: str, course_id: str) -> None:
        if self._course_reader is None:
            return
        if self._course_reader.is_enrolled(user_id, course_id):
            raise AlreadyEnrolledError(course_id)
        info = self._course_reader.get_purchase_info(course_id)
        if info is None:
            return
        if info.owner_id is not None and info.owner_id == user_id:
            raise PaymentNotAllowedError("No puedes pagar tu propio curso.")
        if not info.requires_payment:
            raise PaymentNotAllowedError(
                "Este curso es gratuito: inscríbete sin pagar."
            )

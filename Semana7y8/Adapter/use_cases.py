
from app.modules.payments.application.dtos import PaymentRequestDTO

from app.modules.payments.domain.adapter import (
    PaymentGatewayPort,
    StripePaymentAdapter,
    WompiPaymentAdapter,
)


class ProcessPaymentUseCase:
    """
    Caso de uso para procesar pagos.

    El caso de uso trabaja contra PaymentGatewayPort,
    por lo que no depende directamente de Stripe o Wompi.
    """

    _adapters: dict[str, type[PaymentGatewayPort]] = {
        "stripe": StripePaymentAdapter,
        "wompi": WompiPaymentAdapter,
    }

    def execute(self, dto: PaymentRequestDTO):

        adapter_class = self._adapters.get(dto.gateway)

        if not adapter_class:
            raise ValueError(
                f"Pasarela no soportada: {dto.gateway}"
            )

        adapter = adapter_class()

        return adapter.process_payment(
            amount=dto.amount,
            currency=dto.currency.upper(),
            customer_email=dto.customer_email,
        )
    
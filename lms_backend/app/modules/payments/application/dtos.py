from typing import Literal

from pydantic import Field

from app.shared.application.dtos import MAX_MONEY_AMOUNT, StrictDTO


class PaymentRequestDTO(StrictDTO):
    """Solicitud de pago de un curso.

    El email del cliente y el id de usuario NO vienen en el cuerpo: se toman
    del token del usuario autenticado.
    """

    # StrictDTO rechaza Infinity/NaN (422) y `le` acota el monto.
    amount: float = Field(gt=0, le=MAX_MONEY_AMOUNT)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    gateway: Literal["stripe", "wompi"]
    course_id: str = Field(min_length=1)

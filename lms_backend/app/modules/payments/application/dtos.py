from typing import Literal

from pydantic import BaseModel, Field


class PaymentRequestDTO(BaseModel):
    """Solicitud de pago de un curso.

    El email del cliente y el id de usuario NO vienen en el cuerpo: se toman
    del token del usuario autenticado.
    """

    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    gateway: Literal["stripe", "wompi"]
    course_id: str = Field(min_length=1)

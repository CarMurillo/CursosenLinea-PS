from typing import Literal

from pydantic import BaseModel, Field


class PaymentRequestDTO(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    customer_email: str
    gateway: Literal["stripe", "wompi"]
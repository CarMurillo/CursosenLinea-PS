"""
Módulo: Payments - Capa de Dominio
Entidad Payment: registro de un intento de pago de un usuario por un curso.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Payment:
    user_id: str
    course_id: str
    amount: float
    currency: str
    gateway: str
    status: PaymentStatus
    transaction_id: str = ""
    message: str = ""
    payment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def is_approved(self) -> bool:
        return self.status == PaymentStatus.APPROVED

    def to_dict(self) -> dict:
        return {
            "payment_id": self.payment_id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "amount": self.amount,
            "currency": self.currency,
            "gateway": self.gateway,
            "status": self.status.value,
            "transaction_id": self.transaction_id,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
        }

from typing import List

from app.modules.payments.domain.models import Payment
from app.modules.payments.domain.ports import PaymentRepository


class InMemoryPaymentRepository(PaymentRepository):
    """Adaptador en memoria del puerto PaymentRepository."""

    def __init__(self):
        self._payments: List[Payment] = []

    def save(self, payment: Payment) -> Payment:
        self._payments.append(payment)
        return payment

    def list_by_user(self, user_id: str) -> List[Payment]:
        return [p for p in self._payments if p.user_id == user_id]

    def has_approved_payment(self, user_id: str, course_id: str) -> bool:
        return any(
            p.is_approved and p.user_id == user_id and p.course_id == course_id
            for p in self._payments
        )

    def count(self) -> int:
        return len(self._payments)

    def clear(self) -> None:
        self._payments.clear()



# La instancia compartida la crea el composition root:
# app/shared/infrastructure/container.py (`container.payment_repository`).


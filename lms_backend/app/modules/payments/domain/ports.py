"""
Módulo: Payments - Puertos del dominio (arquitectura hexagonal).

El puerto de pasarela (PaymentGatewayPort) vive en adapter.py junto a los
adaptadores simulados; aquí se reexporta para que la capa de aplicación
dependa solo de puertos.
"""

from abc import ABC, abstractmethod
from typing import List

from app.modules.payments.domain.adapter import PaymentGatewayPort, PaymentResult
from app.modules.payments.domain.models import Payment

__all__ = ["PaymentGatewayPort", "PaymentResult", "PaymentRepository"]


class PaymentRepository(ABC):
    """Puerto de persistencia de pagos."""

    @abstractmethod
    def save(self, payment: Payment) -> Payment:
        pass

    @abstractmethod
    def list_by_user(self, user_id: str) -> List[Payment]:
        pass

    @abstractmethod
    def has_approved_payment(self, user_id: str, course_id: str) -> bool:
        pass

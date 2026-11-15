"""
Módulo: Payments - Puertos del dominio (arquitectura hexagonal).

El puerto de pasarela (PaymentGatewayPort) vive en adapter.py junto a los
adaptadores simulados; aquí se reexporta para que la capa de aplicación
dependa solo de puertos.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from app.modules.payments.domain.adapter import PaymentGatewayPort, PaymentResult
from app.modules.payments.domain.models import Payment

__all__ = [
    "CoursePurchaseInfo",
    "CoursePurchaseReaderPort",
    "PaymentGatewayPort",
    "PaymentResult",
    "PaymentRepository",
]


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



@dataclass(frozen=True)
class CoursePurchaseInfo:
    """Lo que pagos necesita saber de un curso para decidir si se puede cobrar.

    Vista de solo lectura: payments no importa el módulo de cursos; el
    composition root adapta `CourseRepository` a este puerto.
    """

    course_id: str
    owner_id: Optional[str]
    requires_payment: bool
    price: float


class CoursePurchaseReaderPort(ABC):
    """Puerto de lectura de cursos/inscripciones usado por ProcessPaymentUseCase."""

    @abstractmethod
    def get_purchase_info(self, course_id: str) -> Optional[CoursePurchaseInfo]:
        pass

    @abstractmethod
    def is_enrolled(self, user_id: str, course_id: str) -> bool:
        pass

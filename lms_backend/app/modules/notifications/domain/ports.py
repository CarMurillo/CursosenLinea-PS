"""Puertos del módulo de notificaciones.

El puerto del log de auditoría (`AuditLogRepository`) vive en
`app/shared/domain/observers.py` porque lo usa el observador compartido; se
reexporta aquí para que este módulo dependa solo de sus puertos.
"""

from abc import ABC, abstractmethod
from typing import List

from app.modules.notifications.domain.models import Notification
from app.shared.domain.observers import AuditEntry, AuditLogRepository

__all__ = ["AuditEntry", "AuditLogRepository", "NotificationRepository"]


class NotificationRepository(ABC):
    @abstractmethod
    def add(self, notification: Notification) -> Notification: ...

    @abstractmethod
    def list_by_user(self, user_id: str) -> List[Notification]:
        """Más recientes primero."""

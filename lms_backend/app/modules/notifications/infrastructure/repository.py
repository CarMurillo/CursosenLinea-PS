"""Adaptadores en memoria de notificaciones y auditoría.

Las instancias compartidas se crean en el composition root
(`app/shared/infrastructure/container.py`).
"""

import threading
from typing import List, Optional

from app.modules.notifications.domain.models import Notification
from app.modules.notifications.domain.ports import (
    AuditEntry,
    AuditLogRepository,
    NotificationRepository,
)


class InMemoryNotificationRepository(NotificationRepository):
    def __init__(self):
        self._items: List[Notification] = []
        self._lock = threading.Lock()

    def add(self, notification: Notification) -> Notification:
        with self._lock:
            self._items.append(notification)
        return notification

    def list_by_user(self, user_id: str) -> List[Notification]:
        return [n for n in reversed(self._items) if n.user_id == user_id]

    def count(self) -> int:
        with self._lock:
            return len(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


class InMemoryAuditLogRepository(AuditLogRepository):
    def __init__(self):
        self._entries: List[AuditEntry] = []
        self._lock = threading.Lock()

    def append(self, entry: AuditEntry) -> None:
        with self._lock:
            self._entries.append(entry)

    def list_entries(
        self, event_type: Optional[str] = None, limit: Optional[int] = None
    ) -> List[AuditEntry]:
        items = [
            e for e in reversed(self._entries)
            if event_type is None or e.event_type == event_type
        ]
        return items[:limit] if limit is not None else items

    def count(self) -> int:
        with self._lock:
            return len(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

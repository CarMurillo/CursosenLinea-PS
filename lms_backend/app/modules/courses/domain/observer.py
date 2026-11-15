"""
Módulo de COMPATIBILIDAD del patrón Observer.

La implementación real vive en:
- `app/shared/domain/events.py` (EventType, DomainEvent, Observer, Subject).
- `app/shared/domain/observers.py` (EmailNotificationObserver, AuditLogObserver).

Se conservan los nombres históricos importados desde aquí; `LoggingObserver`
es un alias de `AuditLogObserver`.
"""

from app.shared.domain.events import (
    DomainEvent,
    EventPublisher,
    EventType,
    Observer,
    Subject,
    publish_event,
)
from app.shared.domain.observers import (
    AuditEntry,
    AuditLogObserver,
    AuditLogRepository,
    EmailNotificationObserver,
)

LoggingObserver = AuditLogObserver

__all__ = [
    "AuditEntry",
    "AuditLogObserver",
    "AuditLogRepository",
    "DomainEvent",
    "EmailNotificationObserver",
    "EventPublisher",
    "EventType",
    "LoggingObserver",
    "Observer",
    "Subject",
    "publish_event",
]

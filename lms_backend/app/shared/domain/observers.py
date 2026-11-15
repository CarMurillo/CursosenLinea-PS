"""
Observadores concretos SIN dependencias de infraestructura.

- `EmailNotificationObserver`: correo simulado (`print` + registro en memoria).
- `AuditLogObserver`: registra cada evento en un log consultable a través del
  puerto `AuditLogRepository` (inyectado). Antes se llamaba `LoggingObserver`.

Los observadores que necesitan datos de otros módulos (inscripción, in-app,
certificados, perfil de recomendaciones) viven en la capa `application` de
su módulo y reciben sus dependencias por constructor.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from app.shared.domain.events import DomainEvent, EventType, Observer

logger = logging.getLogger(__name__)


# ============================================================ EMAIL (simulado)

def _enrolled_mail(event: DomainEvent) -> tuple[str, str]:
    name = event.payload.get("student_name") or event.user_id
    title = event.payload.get("course_title", "")
    # Mensaje histórico: lo verifica test_courses_api con capsys.
    return name, f"Inscripción confirmada a '{title}'."


def _payment_mail(event: DomainEvent) -> tuple[str, str]:
    to = event.payload.get("customer_email") or event.user_id
    return to, (
        f"Pago aprobado ({event.payload.get('amount')} "
        f"{event.payload.get('currency')}) para el curso {event.course_id}."
    )


def _certificate_mail(event: DomainEvent) -> tuple[str, str]:
    return event.user_id, (
        f"Tu certificado {event.payload.get('certificate_id')} está listo."
    )


class EmailNotificationObserver(Observer):
    """Envía (simula) correos para los eventos que tienen plantilla."""

    TEMPLATES: Dict[EventType, Callable[[DomainEvent], tuple[str, str]]] = {
        EventType.STUDENT_ENROLLED: _enrolled_mail,
        EventType.PAYMENT_APPROVED: _payment_mail,
        EventType.CERTIFICATE_ISSUED: _certificate_mail,
    }

    def __init__(self) -> None:
        self.sent: List[dict] = []

    @classmethod
    def subscribed_events(cls) -> List[EventType]:
        return list(cls.TEMPLATES)

    def update(self, event: DomainEvent) -> None:
        template = self.TEMPLATES.get(event.event_type)
        if template is None:
            return
        recipient, body = template(event)
        print(f"  Enviando correo a {recipient}: {body}")
        self.sent.append({"to": recipient, "body": body, "event_id": event.event_id})


# ================================================================== AUDITORÍA

@dataclass(frozen=True)
class AuditEntry:
    event_id: str
    event_type: str
    occurred_at: str
    user_id: Optional[str]
    course_id: Optional[str]
    payload: dict = field(default_factory=dict)

    @classmethod
    def from_event(cls, event: DomainEvent) -> "AuditEntry":
        data = event.to_dict()
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            occurred_at=data["occurred_at"],
            user_id=data["user_id"],
            course_id=data["course_id"],
            payload=data["payload"],
        )

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "payload": dict(self.payload),
        }


class AuditLogRepository(ABC):
    """Puerto del log de auditoría."""

    @abstractmethod
    def append(self, entry: AuditEntry) -> None: ...

    @abstractmethod
    def list_entries(
        self, event_type: Optional[str] = None, limit: Optional[int] = None
    ) -> List[AuditEntry]:
        """Entradas más recientes primero."""


class _LocalAuditLog(AuditLogRepository):
    """Respaldo en memoria si no se inyecta repositorio (uso aislado/tests)."""

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    def append(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def list_entries(self, event_type=None, limit=None) -> List[AuditEntry]:
        items = [
            e for e in reversed(self._entries)
            if event_type is None or e.event_type == event_type
        ]
        return items[:limit] if limit is not None else items


class AuditLogObserver(Observer):
    """Registra TODOS los eventos (suscríbelo sin filtro)."""

    def __init__(self, repository: Optional[AuditLogRepository] = None) -> None:
        self._repository = repository or _LocalAuditLog()

    @property
    def repository(self) -> AuditLogRepository:
        return self._repository

    def update(self, event: DomainEvent) -> None:
        self._repository.append(AuditEntry.from_event(event))
        logger.info(
            "[AUDITORÍA] %s user=%s course=%s",
            event.event_type.value, event.user_id, event.course_id,
        )

    def entries(self, event_type: Optional[str] = None) -> List[AuditEntry]:
        return self._repository.list_entries(event_type=event_type)

"""
Eventos del dominio y patrón Observer (GoF) compartidos por todos los módulos.

- `EventType`: catálogo cerrado de eventos del LMS.
- `DomainEvent`: hecho inmutable que ya ocurrió (dataclass frozen).
- `Observer`: interfaz de los suscriptores (`update(event)`).
- `Subject`: bus de eventos. `attach(observer, event_types=None)` permite
  suscribirse a todos los eventos o solo a algunos tipos; `detach` y `notify`.

Garantías del `Subject`:
1. Un observador que lanza una excepción se registra con `logging` y NO
   detiene la difusión a los demás ni se propaga al publicador.
2. Los observadores pueden publicar eventos encadenados (p. ej.
   PAYMENT_APPROVED -> inscripción -> STUDENT_ENROLLED). Para evitar bucles
   infinitos hay dos guardas:
   - Reentrada: un observador no vuelve a recibir un evento del MISMO tipo
     mientras todavía está procesando uno de ese tipo (se omite y se avisa).
   - Profundidad: la cadena de publicaciones anidadas no supera `max_depth`.
   El estado de las guardas es por hilo (FastAPI atiende endpoints síncronos
   en un pool de hilos y el bus es compartido).

Este módulo es dominio puro: no importa FastAPI, SQLAlchemy ni infraestructura.
"""

from __future__ import annotations

import logging
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, List, Mapping, Optional, Protocol, Tuple

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    COURSE_PUBLISHED = "course_published"
    STUDENT_ENROLLED = "student_enrolled"
    PAYMENT_APPROVED = "payment_approved"
    LESSON_COMPLETED = "lesson_completed"
    ASSESSMENT_SUBMITTED = "assessment_submitted"
    ASSESSMENT_GRADED = "assessment_graded"
    CERTIFICATE_ISSUED = "certificate_issued"
    LIVE_SESSION_RECORDED = "live_session_recorded"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DomainEvent:
    """Hecho del dominio. Inmutable: el `payload` se congela en solo lectura."""

    event_type: EventType
    _: KW_ONLY
    user_id: Optional[str] = None
    course_id: Optional[str] = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=_utc_now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, EventType):
            object.__setattr__(self, "event_type", EventType(self.event_type))
        object.__setattr__(
            self, "payload", MappingProxyType(dict(self.payload or {}))
        )

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "occurred_at": self.occurred_at.isoformat(),
            "user_id": self.user_id,
            "course_id": self.course_id,
            "payload": dict(self.payload),
        }


class Observer(ABC):
    """Suscriptor del bus de eventos."""

    @abstractmethod
    def update(self, event: DomainEvent) -> None:
        """Reacciona a un evento. No debe asumir orden entre observadores."""


class EventPublisher(Protocol):
    """Puerto mínimo que necesitan los casos de uso para publicar eventos."""

    def notify(self, event: DomainEvent) -> None: ...


_Subscription = Tuple[Observer, Optional[frozenset]]


class Subject:
    """Bus de eventos (sujeto del patrón Observer)."""

    DEFAULT_MAX_DEPTH = 8

    def __init__(self, max_depth: int = DEFAULT_MAX_DEPTH):
        self._subscriptions: List[_Subscription] = []
        self._max_depth = max_depth
        self._lock = threading.RLock()
        self._local = threading.local()

    # ------------------------------------------------------------ suscripción

    def attach(
        self,
        observer: Observer,
        event_types: Optional[Iterable[EventType]] = None,
    ) -> None:
        """Suscribe `observer`. `event_types=None` = todos los eventos.

        Volver a adjuntar el mismo observador reemplaza su filtro (no duplica).
        """
        types = (
            frozenset(EventType(t) for t in event_types)
            if event_types is not None
            else None
        )
        with self._lock:
            self._subscriptions = [
                (obs, t) for obs, t in self._subscriptions if obs is not observer
            ]
            self._subscriptions.append((observer, types))

    def detach(self, observer: Observer) -> None:
        with self._lock:
            self._subscriptions = [
                (obs, t) for obs, t in self._subscriptions if obs is not observer
            ]

    def clear(self) -> None:
        """Quita todos los observadores (útil para reconfigurar el bus)."""
        with self._lock:
            self._subscriptions = []

    @property
    def observers(self) -> List[Observer]:
        return [obs for obs, _ in self._subscriptions]

    def is_attached(self, observer: Observer) -> bool:
        return any(obs is observer for obs, _ in self._subscriptions)

    # --------------------------------------------------------------- difusión

    def _guard_state(self):
        local = self._local
        if not hasattr(local, "depth"):
            local.depth = 0
            local.active = set()
        return local

    def notify(self, event: DomainEvent) -> None:
        state = self._guard_state()
        if state.depth >= self._max_depth:
            logger.warning(
                "Evento %s descartado: profundidad máxima (%d) de eventos "
                "encadenados alcanzada.",
                event.event_type.value,
                self._max_depth,
            )
            return

        with self._lock:
            subscriptions = list(self._subscriptions)

        state.depth += 1
        try:
            for observer, types in subscriptions:
                if types is not None and event.event_type not in types:
                    continue
                key = (id(observer), event.event_type)
                if key in state.active:
                    logger.warning(
                        "Reentrada evitada: %s ya procesa un evento %s.",
                        type(observer).__name__,
                        event.event_type.value,
                    )
                    continue
                state.active.add(key)
                try:
                    observer.update(event)
                except Exception:  # noqa: BLE001 - aislamiento deliberado
                    logger.exception(
                        "El observador %s falló con el evento %s; se continúa "
                        "con los demás.",
                        type(observer).__name__,
                        event.event_type.value,
                    )
                finally:
                    state.active.discard(key)
        finally:
            state.depth -= 1

    # Alias semántico: los casos de uso "publican" eventos.
    publish = notify


def publish_event(publisher: Optional[EventPublisher], event: DomainEvent) -> None:
    """Publica si hay bus inyectado (los casos de uso lo reciben opcional)."""
    if publisher is not None:
        publisher.notify(event)

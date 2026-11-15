"""Observador de notificaciones in-app (una bandeja por usuario)."""

from typing import Callable, Dict, Iterable, List, Optional, Tuple

from app.modules.notifications.domain.models import Notification
from app.modules.notifications.domain.ports import NotificationRepository
from app.shared.domain.events import DomainEvent, EventType, Observer

# Resuelve los destinatarios de eventos "de curso" (p. ej. grabación lista).
CourseMembersResolver = Callable[[str], Iterable[str]]


def _title(event: DomainEvent) -> str:
    return event.payload.get("course_title") or event.course_id or ""


_TEMPLATES: Dict[EventType, Callable[[DomainEvent], Tuple[str, str]]] = {
    EventType.COURSE_PUBLISHED: lambda e: (
        "Curso publicado", f"Tu curso '{_title(e)}' ya está publicado."),
    EventType.STUDENT_ENROLLED: lambda e: (
        "Inscripción confirmada", f"Te inscribiste en '{_title(e)}'."),
    EventType.PAYMENT_APPROVED: lambda e: (
        "Pago aprobado",
        f"Pago de {e.payload.get('amount')} {e.payload.get('currency')} "
        f"aprobado para '{_title(e)}'."),
    EventType.ASSESSMENT_GRADED: lambda e: (
        "Evaluación calificada",
        f"Obtuviste {e.payload.get('score')} puntos "
        f"({'aprobado' if e.payload.get('passed') else 'no aprobado'})."),
    EventType.CERTIFICATE_ISSUED: lambda e: (
        "Certificado emitido",
        f"Ya puedes descargar tu certificado de '{_title(e)}'."),
    EventType.LIVE_SESSION_RECORDED: lambda e: (
        "Grabación disponible",
        f"La grabación de '{e.payload.get('session_title', 'la clase')}' "
        f"está lista."),
}

# Eventos que se notifican a los miembros del curso, no solo a `user_id`.
_COURSE_WIDE = {EventType.LIVE_SESSION_RECORDED}


class InAppNotificationObserver(Observer):
    def __init__(
        self,
        repository: NotificationRepository,
        course_members: Optional[CourseMembersResolver] = None,
    ):
        self._repository = repository
        self._course_members = course_members

    @staticmethod
    def subscribed_events() -> List[EventType]:
        return list(_TEMPLATES)

    def _recipients(self, event: DomainEvent) -> List[str]:
        recipients: List[str] = []
        if event.user_id:
            recipients.append(event.user_id)
        if (
            event.event_type in _COURSE_WIDE
            and event.course_id
            and self._course_members is not None
        ):
            recipients.extend(self._course_members(event.course_id))
        return list(dict.fromkeys(recipients))  # sin duplicados, en orden

    def update(self, event: DomainEvent) -> None:
        template = _TEMPLATES.get(event.event_type)
        if template is None:
            return
        title, message = template(event)
        for user_id in self._recipients(event):
            self._repository.add(Notification(
                user_id=user_id,
                title=title,
                message=message,
                event_type=event.event_type.value,
                course_id=event.course_id,
            ))

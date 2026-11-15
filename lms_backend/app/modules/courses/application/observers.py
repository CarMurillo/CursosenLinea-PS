"""Observadores de la capa de aplicación del módulo de cursos."""

import logging
from typing import Callable, List, Optional

from app.modules.courses.application.use_cases import (
    AlreadyEnrolledError,
    CourseNotFoundError,
)
from app.shared.domain.events import DomainEvent, EventType, Observer

logger = logging.getLogger(__name__)

# Firma de EnrollStudentUseCase.execute(course_id, user_id, student_name).
EnrollFunction = Callable[[str, str, Optional[str]], object]


class AutoEnrollOnPaymentObserver(Observer):
    """PAYMENT_APPROVED -> inscribe al estudiante en el curso pagado.

    Recibe por inyección la función de inscripción (normalmente
    `EnrollStudentUseCase(...).execute`, construido con el mismo bus, de modo
    que la inscripción publica a su vez STUDENT_ENROLLED). Es idempotente:
    si el usuario ya estaba inscrito no hace nada.
    """

    def __init__(self, enroll: EnrollFunction):
        self._enroll = enroll

    @staticmethod
    def subscribed_events() -> List[EventType]:
        return [EventType.PAYMENT_APPROVED]

    def update(self, event: DomainEvent) -> None:
        if event.event_type != EventType.PAYMENT_APPROVED:
            return
        if not event.user_id or not event.course_id:
            logger.warning("PAYMENT_APPROVED sin user_id/course_id: %s", event.event_id)
            return
        try:
            self._enroll(
                event.course_id,
                event.user_id,
                event.payload.get("customer_name"),
            )
        except AlreadyEnrolledError:
            logger.info(
                "Auto-inscripción omitida: %s ya estaba inscrito en %s.",
                event.user_id, event.course_id,
            )
        except CourseNotFoundError:
            logger.warning(
                "Auto-inscripción fallida: el curso %s no existe.", event.course_id
            )

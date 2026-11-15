"""RecommendationProfileObserver: mantiene el perfil de aprendizaje."""

from typing import Callable, Dict, List

from app.modules.recommendations.domain.ports import LearningProfilePort
from app.shared.domain.events import DomainEvent, EventType, Observer


class RecommendationProfileObserver(Observer):
    """Traduce eventos de progreso/desempeño a actualizaciones del perfil."""

    def __init__(self, profiles: LearningProfilePort):
        self._profiles = profiles
        self._handlers: Dict[EventType, Callable[[DomainEvent], None]] = {
            EventType.STUDENT_ENROLLED: lambda e: self._profiles.record_enrollment(
                e.user_id, e.course_id),
            EventType.LESSON_COMPLETED: lambda e: self._profiles.record_lesson_completed(
                e.user_id, e.course_id, e.payload.get("lesson_id")),
            EventType.ASSESSMENT_GRADED: lambda e: self._profiles.record_assessment(
                e.user_id, e.course_id, e.payload),
            EventType.CERTIFICATE_ISSUED: lambda e: self._profiles.record_certificate(
                e.user_id, e.course_id),
        }

    @staticmethod
    def subscribed_events() -> List[EventType]:
        return [
            EventType.STUDENT_ENROLLED,
            EventType.LESSON_COMPLETED,
            EventType.ASSESSMENT_GRADED,
            EventType.CERTIFICATE_ISSUED,
        ]

    def update(self, event: DomainEvent) -> None:
        handler = self._handlers.get(event.event_type)
        if handler is not None and event.user_id and event.course_id:
            handler(event)

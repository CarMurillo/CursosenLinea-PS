"""
Casos de uso de clases en vivo.

- Programar, iniciar y finalizar: instructor dueño del curso o admin.
- Consultar: dueño/admin o estudiantes inscritos.
- `end` finaliza la reunión y, como la grabación es automática, pasa luego a
  `recorded` y publica LIVE_SESSION_RECORDED (user_id = instructor). El
  observador in-app notifica a los inscritos.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.modules.live_sessions.domain.models import LiveSession
from app.modules.live_sessions.domain.ports import (
    LiveSessionRepository,
    VideoConferencePort,
)
from app.shared.domain.errors import PermissionDenied, ResourceNotFound
from app.shared.domain.events import (
    DomainEvent,
    EventPublisher,
    EventType,
    publish_event,
)
from app.shared.domain.state import CourseCatalogPort, CourseInfo


class LiveSessionService:
    def __init__(
        self,
        repository: LiveSessionRepository,
        courses: CourseCatalogPort,
        conference: VideoConferencePort,
        event_bus: Optional[EventPublisher] = None,
    ):
        self._repository = repository
        self._courses = courses
        self._conference = conference
        self._event_bus = event_bus

    def _course(self, course_id: str) -> CourseInfo:
        course = self._courses.get_course_info(course_id)
        if course is None:
            raise ResourceNotFound("Curso no encontrado")
        return course

    def _session(self, session_id: str) -> LiveSession:
        session = self._repository.get_by_id(session_id)
        if session is None:
            raise ResourceNotFound("Clase en vivo no encontrada")
        return session

    def _managed(self, session_id: str, user_id: str, role: str) -> tuple[LiveSession, CourseInfo]:
        session = self._session(session_id)
        course = self._course(session.course_id)
        if not course.is_managed_by(user_id, role):
            raise PermissionDenied(
                "Solo el instructor dueño del curso puede gestionar la clase."
            )
        return session, course

    # ------------------------------------------------------------ comandos
    def schedule(
        self,
        *,
        course_id: str,
        title: str,
        user_id: str,
        role: str,
        scheduled_at: Optional[datetime] = None,
        duration_minutes: int = 60,
    ) -> LiveSession:
        course = self._course(course_id)
        if not course.is_managed_by(user_id, role):
            raise PermissionDenied(
                "Solo el instructor dueño del curso puede programar clases."
            )
        session_id = LiveSession.new_id()
        room_name, room_url = self._conference.create_room(session_id, title)
        session = LiveSession(
            course_id,
            title,
            instructor_id=course.instructor_id or user_id,
            room_name=room_name,
            room_url=room_url,
            provider=self._conference.provider_name,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            session_id=session_id,
        )
        return self._repository.save(session)

    def start(self, session_id: str, *, user_id: str, role: str) -> LiveSession:
        session, _ = self._managed(session_id, user_id, role)
        session.start(self._conference)            # delega en el estado
        return self._repository.save(session)

    def end(self, session_id: str, *, user_id: str, role: str) -> LiveSession:
        session, course = self._managed(session_id, user_id, role)
        session.end(self._conference)              # live -> ended
        session.record(self._conference)           # ended -> recorded (automática)
        self._repository.save(session)

        publish_event(self._event_bus, DomainEvent(
            EventType.LIVE_SESSION_RECORDED,
            user_id=session.instructor_id,
            course_id=course.course_id,
            payload={
                "session_id": session.session_id,
                "session_title": session.title,
                "recording_url": session.recording_url,
                "course_title": course.title,
            },
        ))
        return session

    # ----------------------------------------------------------- consultas
    def _ensure_can_view(self, course: CourseInfo, user_id: str, role: str) -> None:
        if not (course.is_managed_by(user_id, role) or course.is_enrolled(user_id)):
            raise PermissionDenied("No tienes acceso a las clases de este curso.")

    def get_for_user(self, session_id: str, *, user_id: str, role: str) -> LiveSession:
        session = self._session(session_id)
        self._ensure_can_view(self._course(session.course_id), user_id, role)
        return session

    def list_for_course(self, course_id: str, *, user_id: str, role: str) -> List[LiveSession]:
        course = self._course(course_id)
        self._ensure_can_view(course, user_id, role)
        return self._repository.list_by_course(course_id)

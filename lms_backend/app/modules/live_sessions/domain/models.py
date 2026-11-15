"""`LiveSession`: contexto del patrón State para clases en vivo."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from app.modules.live_sessions.domain.states import LiveSessionState, ScheduledState

if TYPE_CHECKING:  # pragma: no cover
    from app.modules.live_sessions.domain.ports import VideoConferencePort


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LiveSession:
    def __init__(
        self,
        course_id: str,
        title: str,
        *,
        instructor_id: str,
        room_name: str,
        room_url: str,
        provider: str,
        scheduled_at: Optional[datetime] = None,
        duration_minutes: int = 60,
        session_id: Optional[str] = None,
        state: Optional[LiveSessionState] = None,
    ):
        if not title or not title.strip():
            raise ValueError("La clase en vivo necesita un título.")
        if duration_minutes <= 0:
            raise ValueError("duration_minutes debe ser mayor que 0.")
        self.session_id = session_id or str(uuid.uuid4())
        self.course_id = course_id
        self.title = title.strip()
        self.instructor_id = instructor_id
        self.room_name = room_name
        self.room_url = room_url
        self.provider = provider
        self.scheduled_at = scheduled_at
        self.duration_minutes = duration_minutes
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        self.recording_url: Optional[str] = None
        self.created_at = _now()
        self._state: LiveSessionState = state or ScheduledState()

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())

    # ------------------------------------------------- delegación al estado
    @property
    def state(self) -> LiveSessionState:
        return self._state

    @property
    def state_name(self) -> str:
        return self._state.name

    def start(self, conference: "VideoConferencePort") -> None:
        self._state.start(self, conference)

    def end(self, conference: "VideoConferencePort") -> None:
        self._state.end(self, conference)

    def record(self, conference: "VideoConferencePort") -> None:
        self._state.record(self, conference)

    # -------------------------------------- primitivas (las usan los estados)
    def _transition_to(self, state: LiveSessionState) -> None:
        self._state = state

    def _mark_started(self) -> None:
        self.started_at = _now()

    def _mark_ended(self) -> None:
        self.ended_at = _now()

    def _set_recording(self, url: str) -> None:
        self.recording_url = url

    def to_dict(self) -> dict:
        iso = lambda d: d.isoformat() if d else None  # noqa: E731
        return {
            "id": self.session_id,
            "course_id": self.course_id,
            "title": self.title,
            "instructor_id": self.instructor_id,
            "state": self.state_name,
            "provider": self.provider,
            "room_url": self.room_url,
            "recording_url": self.recording_url,
            "scheduled_at": iso(self.scheduled_at),
            "duration_minutes": self.duration_minutes,
            "started_at": iso(self.started_at),
            "ended_at": iso(self.ended_at),
            "created_at": iso(self.created_at),
        }

"""Puertos del módulo de clases en vivo (dominio puro)."""

from typing import List, Optional, Protocol

from app.modules.live_sessions.domain.models import LiveSession


class VideoConferencePort(Protocol):
    """Proveedor de videoconferencia (Jitsi, Zoom, Meet...). Adapter."""

    provider_name: str

    def create_room(self, session_id: str, title: str) -> tuple[str, str]:
        """Crea la sala y devuelve (room_name, room_url)."""
        ...

    def start_meeting(self, room_name: str) -> None: ...

    def end_meeting(self, room_name: str) -> None: ...

    def get_recording_url(self, room_name: str) -> str:
        """URL de la grabación automática de una reunión ya finalizada."""
        ...


class LiveSessionRepository(Protocol):
    def save(self, session: LiveSession) -> LiveSession: ...

    def get_by_id(self, session_id: str) -> Optional[LiveSession]: ...

    def list_by_course(self, course_id: str) -> List[LiveSession]: ...

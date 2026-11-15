"""
Patrón State (GoF) reutilizado para el ciclo de vida de una clase en vivo.

    ScheduledState --start--> LiveState --end--> EndedState --record--> RecordedState

`LiveSession` (contexto) delega `start`, `end` y `record` en su estado. Las
operaciones que necesitan la videoconferencia reciben el puerto
`VideoConferencePort` (Adapter), así el estado no conoce a Jitsi.
Agregar un estado (p. ej. `CancelledState`) = una clase nueva.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.shared.domain.state import InvalidStateTransition

if TYPE_CHECKING:  # pragma: no cover
    from app.modules.live_sessions.domain.models import LiveSession
    from app.modules.live_sessions.domain.ports import VideoConferencePort


class LiveSessionState(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def start(self, session: "LiveSession", conference: "VideoConferencePort") -> None: ...

    @abstractmethod
    def end(self, session: "LiveSession", conference: "VideoConferencePort") -> None: ...

    @abstractmethod
    def record(self, session: "LiveSession", conference: "VideoConferencePort") -> None: ...

    def _reject(self, action: str, detail: str = "") -> InvalidStateTransition:
        return InvalidStateTransition("la clase en vivo", self.name, action, detail)


class ScheduledState(LiveSessionState):
    name = "scheduled"

    def start(self, session, conference):
        conference.start_meeting(session.room_name)
        session._mark_started()
        session._transition_to(LiveState())

    def end(self, session, conference):
        raise self._reject("finalizar", "La clase aún no ha comenzado.")

    def record(self, session, conference):
        raise self._reject("grabar", "La clase aún no ha comenzado.")


class LiveState(LiveSessionState):
    name = "live"

    def start(self, session, conference):
        raise self._reject("iniciar", "La clase ya está en vivo.")

    def end(self, session, conference):
        conference.end_meeting(session.room_name)
        session._mark_ended()
        session._transition_to(EndedState())

    def record(self, session, conference):
        raise self._reject("grabar", "Finaliza la clase antes de grabarla.")


class EndedState(LiveSessionState):
    name = "ended"

    def start(self, session, conference):
        raise self._reject("iniciar", "La clase ya finalizó.")

    def end(self, session, conference):
        raise self._reject("finalizar", "La clase ya finalizó.")

    def record(self, session, conference):
        session._set_recording(conference.get_recording_url(session.room_name))
        session._transition_to(RecordedState())


class RecordedState(LiveSessionState):
    name = "recorded"

    def start(self, session, conference):
        raise self._reject("iniciar", "La clase ya finalizó y fue grabada.")

    def end(self, session, conference):
        raise self._reject("finalizar", "La clase ya finalizó y fue grabada.")

    def record(self, session, conference):
        raise self._reject("grabar", "La grabación ya existe.")


# Alias en español (nomenclatura usada en el plan del proyecto).
ProgramadaState = ScheduledState
EnVivoState = LiveState
FinalizadaState = EndedState
GrabadaState = RecordedState

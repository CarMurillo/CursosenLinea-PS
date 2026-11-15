"""
Adapter SIMULADO de Jitsi Meet para `VideoConferencePort`.

No usa SDK ni red: genera nombres/URLs de sala deterministas a partir del id
de la sesión y simula la grabación automática al finalizar la reunión.
Cambiar a Zoom/Meet = otro adaptador que cumpla el mismo puerto.
"""

import re
import threading
import unicodedata
from typing import Dict


def _slug(text: str, max_len: int = 40) -> str:
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    )
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return slug[:max_len] or "clase"


class JitsiAdapter:
    provider_name = "jitsi"

    def __init__(
        self,
        base_url: str = "https://meet.jit.si",
        recordings_base_url: str = "https://recordings.lms.local/jitsi",
    ):
        self._base_url = base_url.rstrip("/")
        self._recordings = recordings_base_url.rstrip("/")
        self._meetings: Dict[str, str] = {}      # room_name -> estado simulado
        self._lock = threading.Lock()

    def create_room(self, session_id: str, title: str) -> tuple[str, str]:
        room_name = f"lms-{_slug(title)}-{session_id.replace('-', '')[:8]}"
        with self._lock:
            self._meetings[room_name] = "created"
        return room_name, f"{self._base_url}/{room_name}"

    def start_meeting(self, room_name: str) -> None:
        with self._lock:
            self._meetings[room_name] = "live"

    def end_meeting(self, room_name: str) -> None:
        with self._lock:
            self._meetings[room_name] = "ended"

    def get_recording_url(self, room_name: str) -> str:
        if self._meetings.get(room_name) != "ended":
            raise RuntimeError(f"La reunión {room_name} no ha finalizado.")
        return f"{self._recordings}/{room_name}.mp4"

    def meeting_status(self, room_name: str) -> str | None:
        return self._meetings.get(room_name)

    def clear(self) -> None:
        with self._lock:
            self._meetings.clear()


# Nombre usado en el enunciado del proyecto.
JitsiVideoConferenceAdapter = JitsiAdapter

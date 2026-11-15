import threading
from typing import Dict, List, Optional

from app.modules.live_sessions.domain.models import LiveSession


class InMemoryLiveSessionRepository:
    def __init__(self):
        self._items: Dict[str, LiveSession] = {}
        self._lock = threading.Lock()

    def save(self, session: LiveSession) -> LiveSession:
        with self._lock:
            self._items[session.session_id] = session
        return session

    def get_by_id(self, session_id: str) -> Optional[LiveSession]:
        return self._items.get(session_id)

    def list_by_course(self, course_id: str) -> List[LiveSession]:
        return [s for s in self._items.values() if s.course_id == course_id]

    def count(self) -> int:
        with self._lock:
            return len(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

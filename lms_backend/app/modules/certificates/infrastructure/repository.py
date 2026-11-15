import threading
from typing import Dict, List, Optional, Tuple

from app.modules.certificates.domain.models import Certificate


class InMemoryCertificateRepository:
    def __init__(self):
        self._items: Dict[Tuple[str, str], Certificate] = {}
        self._lock = threading.Lock()

    def add_if_absent(self, certificate: Certificate) -> bool:
        key = (certificate.user_id, certificate.course_id)
        with self._lock:
            if key in self._items:
                return False
            self._items[key] = certificate
            return True

    def get_by_user_and_course(self, user_id: str, course_id: str) -> Optional[Certificate]:
        return self._items.get((user_id, course_id))

    def list_by_user(self, user_id: str) -> List[Certificate]:
        return sorted(
            (c for (uid, _), c in self._items.items() if uid == user_id),
            key=lambda c: c.issued_at,
            reverse=True,
        )

    def get_by_code(self, code: str) -> Optional[Certificate]:
        return next(
            (c for c in self._items.values() if c.verification_code == code), None
        )

    def count(self) -> int:
        with self._lock:
            return len(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

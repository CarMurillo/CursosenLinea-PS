"""Emisor de certificados en memoria (STUB, solo para pruebas aisladas).

La aplicación ya NO lo usa: `container.py` cablea el servicio real
`CertificateService` (application/services.py) con su repositorio. Se
conserva porque `tests/test_observer.py` prueba el observer contra este
doble de prueba que cumple `CertificateIssuerPort`.
"""

import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Tuple


class InMemoryCertificateIssuer:
    def __init__(self):
        self._issued: Dict[Tuple[str, str], dict] = {}
        self._lock = threading.Lock()

    def issue(
        self, user_id: str, course_id: str, details: Mapping[str, Any]
    ) -> Optional[dict]:
        with self._lock:
            if (user_id, course_id) in self._issued:
                return None
            certificate = {
                "certificate_id": str(uuid.uuid4()),
                "user_id": user_id,
                "course_id": course_id,
                "score": details.get("score"),
                "assessment_id": details.get("assessment_id"),
                "issued_at": datetime.now(timezone.utc).isoformat(),
            }
            self._issued[(user_id, course_id)] = certificate
            return certificate

    def list_by_user(self, user_id: str) -> List[dict]:
        return [c for (uid, _), c in self._issued.items() if uid == user_id]

    def clear(self) -> None:
        with self._lock:
            self._issued.clear()

"""Puertos del módulo de certificados.

`CertificateIssuerPort` es el contrato que usa `CertificateIssuerObserver`;
lo implementa `CertificateService` (application/services.py).
"""

from typing import Any, List, Mapping, Optional, Protocol

from app.modules.certificates.domain.models import Certificate


class CertificateIssuerPort(Protocol):
    def issue(
        self, user_id: str, course_id: str, details: Mapping[str, Any]
    ) -> Optional[Mapping[str, Any]]:
        """Emite el certificado y devuelve sus datos (debe incluir
        `certificate_id`). Devuelve None si no se emite: ya existía uno para
        (user_id, course_id) (emisión idempotente) o el curso no otorga
        certificado."""
        ...


class CertificateRepository(Protocol):
    def add_if_absent(self, certificate: Certificate) -> bool:
        """Guarda si no existe otro para (user_id, course_id). Atómico."""
        ...

    def get_by_user_and_course(
        self, user_id: str, course_id: str
    ) -> Optional[Certificate]: ...

    def list_by_user(self, user_id: str) -> List[Certificate]: ...

    def get_by_code(self, code: str) -> Optional[Certificate]: ...

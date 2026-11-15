"""Puerto mínimo de emisión de certificados (lo usa CertificateIssuerObserver).

La fase patron-state completa el módulo (entidad Certificate, repositorio,
`GET /certificates/me`); basta con que su servicio cumpla este contrato.
"""

from typing import Any, Mapping, Optional, Protocol


class CertificateIssuerPort(Protocol):
    def issue(
        self, user_id: str, course_id: str, details: Mapping[str, Any]
    ) -> Optional[Mapping[str, Any]]:
        """Emite el certificado y devuelve sus datos (debe incluir
        `certificate_id`). Devuelve None si ya existía uno para
        (user_id, course_id): la emisión es idempotente."""
        ...

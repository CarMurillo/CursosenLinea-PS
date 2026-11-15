"""Servicio real de emisión y consulta de certificados."""

from __future__ import annotations

from typing import Any, List, Mapping, Optional

from app.modules.certificates.domain.models import Certificate
from app.modules.certificates.domain.ports import CertificateRepository
from app.shared.domain.state import CourseCatalogPort


class CertificateService:
    """Implementa `CertificateIssuerPort`.

    Solo emite si el curso existe y otorga certificado (decorador
    `CertificateCourseDecorator` -> `CourseInfo.has_certificate`). Sin
    catálogo inyectado (pruebas aisladas) emite para cualquier curso.
    La emisión es idempotente por (user_id, course_id).
    """

    def __init__(
        self,
        repository: CertificateRepository,
        courses: Optional[CourseCatalogPort] = None,
    ):
        self._repository = repository
        self._courses = courses

    def issue(
        self, user_id: str, course_id: str, details: Mapping[str, Any]
    ) -> Optional[dict]:
        course_title = details.get("course_title")
        if self._courses is not None:
            course = self._courses.get_course_info(course_id)
            if course is None or not course.has_certificate:
                return None
            course_title = course_title or course.title

        certificate = Certificate(
            user_id=user_id,
            course_id=course_id,
            score=details.get("score"),
            course_title=course_title,
            assessment_id=details.get("assessment_id"),
        )
        if not self._repository.add_if_absent(certificate):
            return None
        return certificate.to_dict()

    def list_by_user(self, user_id: str) -> List[Certificate]:
        return self._repository.list_by_user(user_id)

    def verify(self, code: str) -> Optional[Certificate]:
        return self._repository.get_by_code(code.strip().upper())

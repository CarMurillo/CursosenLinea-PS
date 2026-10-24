
from typing import Callable, Protocol

from app.modules.courses.domain.content_component import ContentComponent


class ContentAccessDenied(PermissionError):
    """El estudiante no tiene derecho a ver el contenido solicitado."""


class AccessPolicy(Protocol):
    def can_access(self, student_id: str | None, course) -> bool: ...


class EnrolledStudentPolicy:
    """Acceso permitido solo si el estudiante está inscrito en el curso."""

    def can_access(self, student_id: str | None, course) -> bool:
        return student_id is not None and student_id in course.enrolled_students


class ProtectedContentProxy(ContentComponent):
    """
    Proxy de protección. Implementa la MISMA interfaz que el sujeto real
    (ContentComponent), por lo que el cliente y el Composite lo usan sin
    saber que existe. La decisión de acceso la toma el proxy mediante una
    política, no un booleano calculado por quien lo invoca.
    El sujeto real se crea de forma perezosa, solo si el acceso es válido.
    """

    def __init__(
        self,
        real_factory: Callable[[], ContentComponent],
        course,
        student_id: str | None,
        policy: AccessPolicy,
        requires_access: bool = True,
    ):
        self._real_factory = real_factory
        self._real: ContentComponent | None = None
        self._course = course
        self._student_id = student_id
        self._policy = policy
        self._requires_access = requires_access

    def _check(self) -> None:
        if self._requires_access and not self._policy.can_access(
            self._student_id, self._course
        ):
            raise ContentAccessDenied(
                "Debes adquirir el curso Premium para acceder a este contenido."
            )

    def _subject(self) -> ContentComponent:
        self._check()
        if self._real is None:
            self._real = self._real_factory()
        return self._real

    def render_content(self) -> str:
        return self._subject().render_content()

    def to_dict(self) -> dict:
        return self._subject().to_dict()

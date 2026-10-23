
from typing import Protocol


class ContentResource(Protocol):
    def get_content(self) -> dict:
        ...


class CourseContentResource:
    """
    Recurso real de ejemplo.
    En el LMS, sus datos pueden proceder del curso o repositorio.
    """

    def __init__(self, title: str, resource_url: str):
        self.title = title
        self.resource_url = resource_url

    def get_content(self) -> dict:
        return {
            "title": self.title,
            "resource_url": self.resource_url,
        }


class PremiumContentProxy:
    """
    Proxy de protección: valida el acceso antes de mostrar
    el recurso real.
    """

    def __init__(
        self,
        resource: ContentResource,
        is_premium: bool,
        has_access: bool,
    ):
        self._resource = resource
        self._is_premium = is_premium
        self._has_access = has_access

    def get_content(self) -> dict:
        if self._is_premium and not self._has_access:
            raise PermissionError(
                "Debes adquirir el curso Premium para acceder "
                "a este contenido."
            )

        return self._resource.get_content()

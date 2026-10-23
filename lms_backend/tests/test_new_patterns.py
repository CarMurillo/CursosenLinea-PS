
import pytest

from app.modules.courses.application.course_facade import CourseFacade
from app.modules.courses.domain.content_flyweight import (
    ContentMetadataFactory,
)
from app.modules.courses.domain.content_proxy import (
    CourseContentResource,
    PremiumContentProxy,
)


def test_flyweight_reutiliza_metadatos():
    first = ContentMetadataFactory.get_metadata("video")
    second = ContentMetadataFactory.get_metadata("video")

    assert first is second
    assert first.content_type == "video"


def test_flyweight_rechaza_tipo_desconocido():
    with pytest.raises(ValueError):
        ContentMetadataFactory.get_metadata("unknown")


def test_proxy_bloquea_contenido_premium():
    resource = CourseContentResource(
        "Python avanzado",
        "/media/python"
    )
    proxy = PremiumContentProxy(
        resource=resource,
        is_premium=True,
        has_access=False,
    )

    with pytest.raises(PermissionError):
        proxy.get_content()


def test_proxy_permite_acceso_autorizado():
    resource = CourseContentResource(
        "Python avanzado",
        "/media/python"
    )
    proxy = PremiumContentProxy(
        resource=resource,
        is_premium=True,
        has_access=True,
    )

    result = proxy.get_content()

    assert result["title"] == "Python avanzado"


def test_proxy_no_bloquea_contenido_no_premium():
    resource = CourseContentResource(
        "Introducción",
        "/media/intro"
    )
    proxy = PremiumContentProxy(
        resource=resource,
        is_premium=False,
        has_access=False,
    )

    assert proxy.get_content()["title"] == "Introducción"


def test_facade_lista_cursos():
    facade = CourseFacade()
    courses = facade.list_courses()

    assert isinstance(courses, list)
    
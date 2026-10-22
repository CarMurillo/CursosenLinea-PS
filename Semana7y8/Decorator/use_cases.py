"""
Casos de uso del módulo de cursos.

Patrones implementados:

- Builder: construcción progresiva de cursos.
- Factory Method: creación del tipo concreto de curso.
- Prototype: clonación de cursos existentes.
- Observer: notificaciones al realizar matrículas.
- Decorator: agregar características adicionales a los cursos.
"""

from app.modules.courses.application.dtos import CourseCreateDTO

from app.modules.courses.domain.builder import CourseBuilder

from app.modules.courses.domain.models import Course

from app.modules.courses.domain.observer import (
    EmailNotificationObserver,
    LoggingObserver,
    Subject,
)

from app.modules.courses.domain.ports import CourseRepository

from app.modules.courses.domain.decorator import (
    CertificateCourseDecorator,
    PremiumCourseDecorator,
)


class CourseNotFoundError(Exception):
    """Se lanza cuando no se encuentra un curso."""
    pass


# ============================================================
# PUBLICAR CURSO
# ============================================================

class PublishCourseUseCase:
    """
    Caso de uso para crear y publicar un curso.

    Builder prepara progresivamente los datos y posteriormente
    utiliza el Factory Method para crear el tipo concreto de curso.
    """

    def __init__(self, repository: CourseRepository):
        self.repository = repository

    def execute(self, dto: CourseCreateDTO) -> Course:
        course = (
            CourseBuilder()
            .set_title(dto.title)
            .set_instructor(dto.instructor)
            .set_price(dto.price)
            .set_course_type(dto.course_type)
            .build()
        )

        # DECORATOR
        if dto.premium:
            course = PremiumCourseDecorator(course)

        if dto.certificate:
            course = CertificateCourseDecorator(course)

        return self.repository.save(course)


# ============================================================
# PROTOTYPE
# ============================================================

class CloneCourseUseCase:
    """
    Caso de uso para duplicar un curso existente.

    Utiliza el patrón Prototype mediante el método clone()
    definido en la entidad Course.
    """

    def __init__(self, repository: CourseRepository):
        self.repository = repository

    def execute(
        self,
        course_id: str,
        new_title: str | None = None,
    ) -> Course:

        # Buscar el curso original
        original_course = self.repository.get_by_id(course_id)

        if not original_course:
            raise CourseNotFoundError(course_id)

        # PROTOTYPE: clonar el curso original
        cloned_course = original_course.clone()

        # Asignar el título al nuevo curso
        if new_title and new_title.strip():
            cloned_course.title = new_title.strip()
        else:
            cloned_course.title = (
                f"{original_course.title} (Copia)"
            )

        # Actualizar el título del contenido, si existe
        content = getattr(cloned_course, "content", None)

        if content is not None:
            content.title = (
                f"Contenido de {cloned_course.title}"
            )

        # Guardar el curso clonado
        return self.repository.save(cloned_course)


# ============================================================
# OBSERVER
# ============================================================

class EnrollStudentUseCase:
    """
    Caso de uso para matricular estudiantes.

    Observer notifica a los observadores cuando un estudiante
    se matricula en un curso.
    """

    def __init__(self, repository: CourseRepository):
        self.repository = repository

        # OBSERVER
        self._notifier = Subject()

        self._notifier.attach(
            EmailNotificationObserver()
        )

        self._notifier.attach(
            LoggingObserver()
        )

    def execute(
        self,
        course_id: str,
        student_name: str,
    ) -> Course:

        # Buscar el curso
        course = self.repository.get_by_id(course_id)

        if not course:
            raise CourseNotFoundError(course_id)

        # Registrar la matrícula
        course.enrolled_students.append(student_name)

        # Notificar a los observadores
        self._notifier.notify(
            student_name,
            course.title,
        )

        return course


# ============================================================
# LISTAR CURSOS
# ============================================================

class ListCoursesUseCase:
    """
    Caso de uso para consultar todos los cursos disponibles.
    """

    def __init__(self, repository: CourseRepository):
        self.repository = repository

    def execute(self) -> list[Course]:
        return self.repository.list_all()
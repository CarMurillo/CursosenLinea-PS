"""
Casos de uso del módulo de cursos.

Patrones implementados:

- Builder: construcción progresiva de cursos.
- Factory Method: creación del tipo concreto de curso.
- Prototype: clonación de cursos existentes.
- Observer: notificaciones al realizar matrículas.
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


class CourseNotFoundError(Exception):
    pass


# ============================================================
# PUBLICAR CURSO
# ============================================================

class PublishCourseUseCase:
    """
    Caso de uso para crear un nuevo curso.

    Builder prepara progresivamente los datos y posteriormente
    utiliza el Factory Method para crear VideoCourse o
    LiveClassCourse.
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
        new_title: str | None = None
    ) -> Course:

        original_course = self.repository.get_by_id(course_id)

        if not original_course:
            raise CourseNotFoundError(course_id)

        # Prototype
        cloned_course = original_course.clone()

        if new_title and new_title.strip():
            cloned_course.title = new_title.strip()
        else:
            cloned_course.title = (
                f"{original_course.title} (Copia)"
            )

        return self.repository.save(cloned_course)


# ============================================================
# OBSERVER
# ============================================================

class EnrollStudentUseCase:
    """
    Caso de uso para matricular estudiantes.
    """

    def __init__(self, repository: CourseRepository):

        self.repository = repository

        # Observer
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
        student_name: str
    ) -> Course:

        course = self.repository.get_by_id(course_id)

        if not course:
            raise CourseNotFoundError(course_id)

        course.enrolled_students.append(student_name)

        self._notifier.notify(
            student_name,
            course.title
        )

        return course


# ============================================================
# LISTAR CURSOS
# ============================================================

class ListCoursesUseCase:

    def __init__(self, repository: CourseRepository):
        self.repository = repository

    def execute(self) -> list[Course]:
        return self.repository.list_all()
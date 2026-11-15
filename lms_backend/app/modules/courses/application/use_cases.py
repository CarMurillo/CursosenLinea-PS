"""
Casos de uso del módulo de cursos.

Patrones implementados:

- Builder: construcción progresiva de cursos.
- Factory Method: creación del tipo concreto de curso.
- Prototype: clonación de cursos existentes.
- Observer: los casos de uso publican eventos de dominio (COURSE_PUBLISHED,
  STUDENT_ENROLLED) en el bus único inyectado desde el composition root.
"""

from typing import Optional, Protocol

from app.modules.courses.application.dtos import CourseCreateDTO
from app.modules.courses.domain.builder import CourseBuilder
from app.modules.courses.domain.models import Course
from app.modules.courses.domain.ports import CourseRepository
from app.shared.domain.events import (
    DomainEvent,
    EventPublisher,
    EventType,
    publish_event,
)

from app.modules.courses.domain.decorator import (
    CertificateCourseDecorator,
    PremiumCourseDecorator,
)


class CourseNotFoundError(Exception):
    pass


class AlreadyEnrolledError(Exception):
    """El usuario ya está inscrito en el curso (HTTP 409)."""


class PaymentRequiredError(Exception):
    """Curso premium/de pago sin pago aprobado del usuario (HTTP 403)."""


class ApprovedPaymentChecker(Protocol):
    """Puerto mínimo que necesita la inscripción (lo cumple PaymentRepository)."""

    def has_approved_payment(self, user_id: str, course_id: str) -> bool: ...


def course_requires_payment(course: Course) -> bool:
    """Un curso exige pago si es Premium o tiene precio mayor que cero."""
    details = course.get_details()
    return bool(details.get("premium")) or float(course.price or 0) > 0


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

    def __init__(
        self,
        repository: CourseRepository,
        event_bus: Optional[EventPublisher] = None,
    ):
        self.repository = repository
        # Observer: bus único inyectado; publica COURSE_PUBLISHED.
        self.event_bus = event_bus

    def execute(
        self,
        dto: CourseCreateDTO,
        instructor_id: str | None = None,
        instructor_name: str | None = None,
    ) -> Course:

        course = (
            CourseBuilder()
            .set_title(dto.title)
            .set_instructor(instructor_name or dto.instructor or "")
            .set_price(dto.price)
            .set_course_type(dto.course_type)
            .build()
        )
        course.instructor_id = instructor_id

        # DECORATOR: características opcionales
        if dto.premium:
            course = PremiumCourseDecorator(course)

        if dto.certificate:
            course = CertificateCourseDecorator(course)

        saved = self.repository.save(course)

        details = saved.get_details()
        publish_event(self.event_bus, DomainEvent(
            EventType.COURSE_PUBLISHED,
            user_id=instructor_id,
            course_id=saved.course_id,
            payload={
                "course_title": saved.title,
                "instructor": saved.instructor,
                "price": saved.price,
                "premium": bool(details.get("premium")),
                "certificate": bool(details.get("certificate")),
            },
        ))

        return saved


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

        # La raíz del Composite debe reflejar el nuevo título.
        cloned_course.content.title = (
            f"Contenido de {cloned_course.title}"
        )

        return self.repository.save(cloned_course)


# ============================================================
# OBSERVER
# ============================================================

class EnrollStudentUseCase:
    """
    Caso de uso para matricular estudiantes.

    - La identidad es el id del usuario autenticado (no un nombre libre).
    - Inscripción duplicada -> AlreadyEnrolledError.
    - Curso premium o con precio sin pago aprobado -> PaymentRequiredError.
    - Observer: publica STUDENT_ENROLLED en el bus único INYECTADO (ya no
      se crea un Subject por request). Sin bus, no se notifica.
    """

    def __init__(
        self,
        repository: CourseRepository,
        payment_checker: Optional[ApprovedPaymentChecker] = None,
        event_bus: Optional[EventPublisher] = None,
    ):
        self.repository = repository
        self._payment_checker = payment_checker
        self.event_bus = event_bus

    def execute(
        self,
        course_id: str,
        user_id: str,
        student_name: str | None = None,
    ) -> Course:

        course = self.repository.get_by_id(course_id)

        if not course:
            raise CourseNotFoundError(course_id)

        if user_id in course.enrolled_students:
            raise AlreadyEnrolledError(course_id)

        if course_requires_payment(course):
            paid = (
                self._payment_checker is not None
                and self._payment_checker.has_approved_payment(
                    user_id, course_id
                )
            )
            if not paid:
                raise PaymentRequiredError(course_id)

        course.enrolled_students.append(user_id)

        publish_event(self.event_bus, DomainEvent(
            EventType.STUDENT_ENROLLED,
            user_id=user_id,
            course_id=course.course_id,
            payload={
                "student_name": student_name or user_id,
                "course_title": course.title,
            },
        ))

        return course


# ============================================================
# LISTAR CURSOS
# ============================================================

class ListCoursesUseCase:

    def __init__(self, repository: CourseRepository):
        self.repository = repository

    def execute(self) -> list[Course]:
        return self.repository.list_all()


class ListEnrolledCoursesUseCase:
    """Cursos en los que está inscrito un usuario (por user_id)."""

    def __init__(self, repository: CourseRepository):
        self.repository = repository

    def execute(self, user_id: str) -> list[Course]:
        return [
            course
            for course in self.repository.list_all()
            if user_id in course.enrolled_students
        ]

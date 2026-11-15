from typing import Any, Optional

from app.modules.courses.application.dtos import CourseCreateDTO
from app.modules.courses.application.use_cases import (
    ApprovedPaymentChecker,
    CloneCourseUseCase,
    CourseNotFoundError,
    EnrollStudentUseCase,
    ListCoursesUseCase,
    ListEnrolledCoursesUseCase,
    PublishCourseUseCase,
)
from app.modules.courses.domain.models import Course
from app.modules.courses.domain.ports import CourseRepository


class CourseFacade:
    """
    Facade: interfaz única y simplificada para las operaciones de cursos.

    Depende del PUERTO CourseRepository (no del adaptador concreto), de modo
    que la capa de aplicación no importa nada de infraestructura. El
    notificador (Observer), el verificador de pagos y el bus de eventos se
    inyectan desde el composition root; todos son opcionales.
    """

    def __init__(
        self,
        repository: CourseRepository,
        notifier: Optional[Any] = None,
        payment_checker: Optional[ApprovedPaymentChecker] = None,
        event_bus: Optional[Any] = None,
    ):
        self._repository = repository
        self._notifier = notifier
        self._payment_checker = payment_checker
        self._event_bus = event_bus

    def list_courses(self) -> list[Course]:
        return ListCoursesUseCase(self._repository).execute()

    def list_enrolled_courses(self, user_id: str) -> list[Course]:
        return ListEnrolledCoursesUseCase(self._repository).execute(user_id)

    def get_course(self, course_id: str) -> Course:
        course = self._repository.get_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(course_id)
        return course

    def create_course(
        self,
        dto: CourseCreateDTO,
        instructor_id: str | None = None,
        instructor_name: str | None = None,
    ) -> Course:
        return PublishCourseUseCase(
            self._repository, event_bus=self._event_bus
        ).execute(dto, instructor_id, instructor_name)

    def clone_course(
        self, course_id: str, new_title: str | None = None
    ) -> Course:
        return CloneCourseUseCase(self._repository).execute(
            course_id, new_title
        )

    def enroll_student(
        self,
        course_id: str,
        user_id: str,
        student_name: str | None = None,
    ) -> Course:
        return EnrollStudentUseCase(
            self._repository,
            notifier=self._notifier,
            payment_checker=self._payment_checker,
            event_bus=self._event_bus,
        ).execute(course_id, user_id, student_name)

from app.modules.courses.application.dtos import CourseCreateDTO
from app.modules.courses.application.use_cases import (
    CloneCourseUseCase,
    CourseNotFoundError,
    EnrollStudentUseCase,
    ListCoursesUseCase,
    PublishCourseUseCase,
)
from app.modules.courses.domain.models import Course
from app.modules.courses.domain.ports import CourseRepository


class CourseFacade:
    """
    Facade: interfaz única y simplificada para las operaciones de cursos.

    Depende del PUERTO CourseRepository (no del adaptador concreto), de modo
    que la capa de aplicación no importa nada de infraestructura.
    """

    def __init__(self, repository: CourseRepository):
        self._repository = repository

    def list_courses(self) -> list[Course]:
        return ListCoursesUseCase(self._repository).execute()

    def get_course(self, course_id: str) -> Course:
        course = self._repository.get_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(course_id)
        return course

    def create_course(self, dto: CourseCreateDTO) -> Course:
        return PublishCourseUseCase(self._repository).execute(dto)

    def clone_course(
        self, course_id: str, new_title: str | None = None
    ) -> Course:
        return CloneCourseUseCase(self._repository).execute(
            course_id, new_title
        )

    def enroll_student(self, course_id: str, student_name: str) -> Course:
        return EnrollStudentUseCase(self._repository).execute(
            course_id, student_name
        )

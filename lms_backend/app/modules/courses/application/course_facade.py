
from app.modules.courses.application.dtos import CourseCreateDTO
from app.modules.courses.application.use_cases import (
    CloneCourseUseCase,
    CourseNotFoundError,
    EnrollStudentUseCase,
    ListCoursesUseCase,
    PublishCourseUseCase,
)
from app.modules.courses.infrastructure.repository import course_repository


class CourseFacade:
    """
    Facade: centraliza las operaciones principales de cursos.
    """

    def __init__(self, repository=None):
        self.repository = repository or course_repository

    def list_courses(self):
        return ListCoursesUseCase(
            self.repository
        ).execute()

    def create_course(self, dto: CourseCreateDTO):
        return PublishCourseUseCase(
            self.repository
        ).execute(dto)

    def clone_course(
        self,
        course_id: str,
        new_title: str | None = None
    ):
        return CloneCourseUseCase(
            self.repository
        ).execute(course_id, new_title)

    def enroll_student(
        self,
        course_id: str,
        student_name: str
    ):
        return EnrollStudentUseCase(
            self.repository
        ).execute(course_id, student_name)

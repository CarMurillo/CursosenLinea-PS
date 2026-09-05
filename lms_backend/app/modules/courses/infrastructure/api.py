from fastapi import APIRouter, HTTPException

from app.modules.courses.application.dtos import CourseCreateDTO, EnrollmentDTO
from app.modules.courses.application.use_cases import (
    CourseNotFoundError,
    EnrollStudentUseCase,
    ListCoursesUseCase,
    PublishCourseUseCase,
)
from app.modules.courses.infrastructure.repository import course_repository

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/")
def list_courses():
    use_case = ListCoursesUseCase(course_repository)
    return [course.get_details() for course in use_case.execute()]


@router.post("/", status_code=201)
def publish_course(dto: CourseCreateDTO):
    """Endpoint para que un instructor publique un módulo de estudio."""
    use_case = PublishCourseUseCase(course_repository)
    course = use_case.execute(dto)
    return course.get_details()


@router.post("/{course_id}/enroll")
def enroll_student(course_id: str, dto: EnrollmentDTO):
    """Endpoint para que un estudiante se inscriba a un curso."""
    use_case = EnrollStudentUseCase(course_repository)
    try:
        course = use_case.execute(course_id, dto.student_name)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    return {
        "status": "success",
        "message": f"Estudiante '{dto.student_name}' inscrito correctamente en '{course.title}'.",
        "course": course.get_details(),
    }
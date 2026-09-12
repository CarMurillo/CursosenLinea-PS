from fastapi import APIRouter, HTTPException

from app.modules.courses.application.dtos import (
    CloneCourseDTO,
    CourseCreateDTO,
    EnrollmentDTO,
)

from app.modules.courses.application.use_cases import (
    CloneCourseUseCase,
    CourseNotFoundError,
    EnrollStudentUseCase,
    ListCoursesUseCase,
    PublishCourseUseCase,
)

from app.modules.courses.infrastructure.repository import (
    course_repository,
)


router = APIRouter(
    prefix="/courses",
    tags=["courses"]
)


# ============================================================
# LISTAR CURSOS
# ============================================================

@router.get("/")
def list_courses():

    use_case = ListCoursesUseCase(
        course_repository
    )

    return [
        course.get_details()
        for course in use_case.execute()
    ]


# ============================================================
# CREAR CURSO
# ============================================================

@router.post("/", status_code=201)
def publish_course(dto: CourseCreateDTO):

    use_case = PublishCourseUseCase(
        course_repository
    )

    try:

        course = use_case.execute(dto)

        return course.get_details()

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# ============================================================
# PROTOTYPE - CLONAR CURSO
# ============================================================

@router.post(
    "/{course_id}/clone",
    status_code=201
)
def clone_course(
    course_id: str,
    dto: CloneCourseDTO
):

    use_case = CloneCourseUseCase(
        course_repository
    )

    try:

        course = use_case.execute(
            course_id,
            dto.new_title
        )

        return course.get_details()

    except CourseNotFoundError:

        raise HTTPException(
            status_code=404,
            detail="Curso no encontrado"
        )


# ============================================================
# INSCRIBIR ESTUDIANTE
# ============================================================

@router.post("/{course_id}/enroll")
def enroll_student(
    course_id: str,
    dto: EnrollmentDTO
):

    use_case = EnrollStudentUseCase(
        course_repository
    )

    try:

        course = use_case.execute(
            course_id,
            dto.student_name
        )

    except CourseNotFoundError:

        raise HTTPException(
            status_code=404,
            detail="Curso no encontrado"
        )

    return {
        "status": "success",
        "message": (
            f"Estudiante '{dto.student_name}' "
            f"inscrito correctamente en "
            f"'{course.title}'."
        ),
        "course": course.get_details(),
    }
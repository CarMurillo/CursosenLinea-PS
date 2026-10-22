from fastapi import APIRouter, HTTPException

from app.modules.courses.application.dtos import (
    CloneCourseDTO,
    CourseCreateDTO,
    EnrollmentDTO,
    LessonCreateDTO,
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

from app.modules.courses.domain.bridge import (
    InteractiveQuizLesson,
    S3StorageProvider,
    VimeoStorageProvider,
    VideoLesson,
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

@router.post(
    "/{course_id}/content/lessons",
    status_code=201
)
def add_lesson(
    course_id: str,
    dto: LessonCreateDTO
):

    course = course_repository.get_by_id(
        course_id
    )

    if not course:

        raise HTTPException(
            status_code=404,
            detail="Curso no encontrado"
        )


    providers = {

        "vimeo":
            VimeoStorageProvider(),

        "s3":
            S3StorageProvider(),

    }


    provider = providers[
        dto.provider
    ]


    if dto.lesson_type == "video":

        lesson = VideoLesson(
            dto.title,
            dto.media_id,
            provider
        )

    else:

        lesson = InteractiveQuizLesson(
            dto.title,
            dto.media_id,
            provider
        )


    course.content.add_lesson(
        dto.module_title,
        lesson
    )


    return {

        "message":
            "Lección agregada correctamente",

        "course_id":
            course.course_id,

        "content":
            course.content.to_dict(),

    }
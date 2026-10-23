
from fastapi import APIRouter, HTTPException

from app.modules.courses.application.dtos import (
    CloneCourseDTO,
    CourseCreateDTO,
    EnrollmentDTO,
    LessonCreateDTO,
)

from app.modules.courses.application.course_facade import (
    CourseFacade,
)

from app.modules.courses.application.use_cases import (
    CourseNotFoundError,
)

from app.modules.courses.domain.bridge import (
    InteractiveQuizLesson,
    S3StorageProvider,
    VimeoStorageProvider,
    VideoLesson,
)

from app.modules.courses.domain.content_proxy import (
    CourseContentResource,
    PremiumContentProxy,
)

router = APIRouter(prefix="/courses", tags=["courses"])

# FACADE: centraliza las operaciones principales de cursos.
facade = CourseFacade()


# ============================================================
# LISTAR CURSOS - FACADE
# ============================================================

@router.get("/")
def list_courses():
    return [
        course.get_details()
        for course in facade.list_courses()
    ]


# ============================================================
# CREAR CURSO - FACADE
# ============================================================

@router.post("/", status_code=201)
def publish_course(dto: CourseCreateDTO):
    try:
        course = facade.create_course(dto)
        return course.get_details()
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ============================================================
# PROTOTYPE: CLONAR CURSO - FACADE
# ============================================================

@router.post("/{course_id}/clone", status_code=201)
def clone_course(course_id: str, dto: CloneCourseDTO):
    try:
        course = facade.clone_course(
            course_id,
            dto.new_title,
        )
        return course.get_details()
    except CourseNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Curso no encontrado",
        )


# ============================================================
# INSCRIBIR ESTUDIANTE - FACADE
# ============================================================

@router.post("/{course_id}/enroll")
def enroll_student(course_id: str, dto: EnrollmentDTO):
    try:
        course = facade.enroll_student(
            course_id,
            dto.student_name,
        )
    except CourseNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Curso no encontrado",
        )

    return {
        "status": "success",
        "message": (
            f"Estudiante '{dto.student_name}' "
            f"inscrito correctamente en '{course.title}'."
        ),
        "course": course.get_details(),
    }


# ============================================================
# BRIDGE + COMPOSITE: AGREGAR CONTENIDO AL CURSO
# ============================================================

@router.post(
    "/{course_id}/content/lessons",
    status_code=201,
)
def add_lesson(course_id: str, dto: LessonCreateDTO):
    course = facade.repository.get_by_id(course_id)

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Curso no encontrado",
        )

    # BRIDGE: proveedor de almacenamiento intercambiable.
    providers = {
        "vimeo": VimeoStorageProvider,
        "s3": S3StorageProvider,
    }

    provider_class = providers.get(dto.provider.lower())

    if provider_class is None:
        raise HTTPException(
            status_code=400,
            detail="Proveedor no válido. Usa 'vimeo' o 's3'.",
        )

    provider = provider_class()

    # BRIDGE: el tipo de lección trabaja con el proveedor elegido.
    if dto.lesson_type.lower() == "video":
        lesson = VideoLesson(
            dto.title,
            dto.media_id,
            provider,
        )
    elif dto.lesson_type.lower() in ("quiz", "interactive_quiz"):
        lesson = InteractiveQuizLesson(
            dto.title,
            dto.media_id,
            provider,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Tipo de lección no válido. Usa 'video' o 'quiz'.",
        )

    # COMPOSITE: se incorpora la lección a la estructura de contenido.
    course.content.add_lesson(
        dto.module_title,
        lesson,
    )

    return {
        "message": "Lección agregada correctamente",
        "course_id": course.course_id,
        "content": course.content.to_dict(),
    }


# ============================================================
# PROXY: DEMOSTRACIÓN DE CONTROL DE ACCESO A CONTENIDO PREMIUM
# ============================================================

@router.get("/demo-content-access")
def demo_content_access(
    premium: bool = True,
    has_access: bool = False,
):
    resource = CourseContentResource(
        title="Lección Premium de Python",
        resource_url="/media/python-avanzado",
    )

    proxy = PremiumContentProxy(
        resource=resource,
        is_premium=premium,
        has_access=has_access,
    )

    try:
        return proxy.get_content()
    except PermissionError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error),
        )

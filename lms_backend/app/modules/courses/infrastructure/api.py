
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.modules.courses.application.dtos import (
    CloneCourseDTO,
    CourseCreateDTO,
    EnrollmentDTO,
    LessonCreateDTO,
)
from app.modules.courses.domain.content_flyweight import (
    ContentMetadataFactory,
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
    ContentAccessDenied,
    EnrolledStudentPolicy,
    ProtectedContentProxy,
)

from app.modules.auth.infrastructure.security import resolve_token
from app.modules.courses.infrastructure.repository import course_repository
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository

router = APIRouter(prefix="/courses", tags=["courses"])

def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Resuelve el usuario a partir de 'Authorization: Bearer <token>'."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    user_id = resolve_token(authorization[7:].strip())
    user = SqlAlchemyUserRepository(db).get_by_id(user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=401, detail="Sesión no válida")
    return user


# FACADE: la infraestructura (composition root) inyecta el adaptador.
facade = CourseFacade(course_repository)


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
    try:
        course = facade.get_course(course_id)
    except CourseNotFoundError:
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
# PROXY: CONTENIDO PROTEGIDO DEL CURSO
# ============================================================

@router.get("/{course_id}/content")
def get_course_content(
    course_id: str,
    user=Depends(get_current_user),
):
    try:
        course = facade.get_course(course_id)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    is_premium = bool(course.get_details().get("premium"))
    is_staff = user.role in ("instructor", "admin")
    full_name = f"{user.first_name} {user.last_name}"

    proxy = ProtectedContentProxy(
        real_factory=lambda: course.content,
        course=course,
        student_id=full_name,   # mismo valor que el front envía al inscribir
        policy=EnrolledStudentPolicy(),
        requires_access=is_premium and not is_staff,
    )

    try:
        return proxy.to_dict()
    except ContentAccessDenied as error:
        raise HTTPException(status_code=403, detail=str(error))


# ============================================================
# FLYWEIGHT: CONSULTAR METADATOS COMPARTIDOS
# ============================================================

@router.get("/content-metadata/{content_type}")
def get_content_metadata(content_type: str):
    try:
        metadata = ContentMetadataFactory.get_metadata(
            content_type
        )

        return {
            "content_type": metadata.content_type,
            "label": metadata.label,
            "icon": metadata.icon,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

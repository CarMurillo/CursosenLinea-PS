
from fastapi import APIRouter, Depends, HTTPException

from app.modules.courses.application.dtos import (
    CloneCourseDTO,
    CourseCreateDTO,
    EnrollmentDTO,
    LessonCreateDTO,
)
from app.modules.courses.domain.content_flyweight import (
    ContentMetadataFactory,
)

from app.modules.courses.application.use_cases import (
    AlreadyEnrolledError,
    CourseNotFoundError,
    PaymentRequiredError,
    course_requires_payment,
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

from app.modules.courses.domain.visitor import (
    ContentSummaryVisitor,
    ExportSyllabusVisitor,
)
from app.modules.progress.application.use_cases import (
    CompleteLessonUseCase,
    GetProgressUseCase,
    LessonNotFoundError,
)
from app.shared.infrastructure.auth_deps import (  # noqa: F401  (reexport)
    get_current_user,
    require_role,
)
from app.shared.infrastructure import container

router = APIRouter(prefix="/courses", tags=["courses"])

# `get_current_user` se reexporta desde aquí por compatibilidad; su
# implementación vive en app/shared/infrastructure/auth_deps.py.
require_staff = require_role("instructor", "admin")


# FACADE: instancia única creada en el composition root (container.py) con
# el repositorio, el bus de eventos único (Observer) y el verificador de pagos.
facade = container.course_facade


def _get_course_or_404(course_id: str):
    try:
        return facade.get_course(course_id)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail="Curso no encontrado")


def _ensure_owner(course, user) -> None:
    """Solo el instructor dueño del curso o un admin pueden modificarlo."""
    if user.role == "admin":
        return
    if course.instructor_id is None or course.instructor_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Solo el instructor dueño del curso puede modificarlo.",
        )


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
# RUTAS LITERALES (declaradas ANTES de las rutas /{course_id})
# ============================================================

@router.get("/me/enrolled")
def list_my_enrolled_courses(user=Depends(get_current_user)):
    """Cursos en los que está inscrito el usuario autenticado."""
    return [
        course.get_details()
        for course in facade.list_enrolled_courses(user.id)
    ]


# FLYWEIGHT: CONSULTAR METADATOS COMPARTIDOS
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


# ============================================================
# CREAR CURSO - FACADE (instructor o admin)
# ============================================================

@router.post("/", status_code=201)
def publish_course(dto: CourseCreateDTO, user=Depends(require_staff)):
    try:
        # El instructor se deriva del token; `dto.instructor` se ignora.
        course = facade.create_course(
            dto,
            instructor_id=user.id,
            instructor_name=f"{user.first_name} {user.last_name}",
        )
        return course.get_details()
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ============================================================
# PROTOTYPE: CLONAR CURSO - FACADE (dueño o admin)
# ============================================================

@router.post("/{course_id}/clone", status_code=201)
def clone_course(
    course_id: str,
    dto: CloneCourseDTO,
    user=Depends(require_staff),
):
    _ensure_owner(_get_course_or_404(course_id), user)
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
# INSCRIBIR ESTUDIANTE - FACADE (usuario autenticado)
# ============================================================

@router.post("/{course_id}/enroll")
def enroll_student(
    course_id: str,
    dto: EnrollmentDTO | None = None,
    user=Depends(get_current_user),
):
    # La identidad sale del token; `dto.student_name` se ignora.
    full_name = f"{user.first_name} {user.last_name}"
    try:
        course = facade.enroll_student(course_id, user.id, full_name)
    except CourseNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Curso no encontrado",
        )
    except AlreadyEnrolledError:
        raise HTTPException(
            status_code=409,
            detail="Ya estás inscrito en este curso.",
        )
    except PaymentRequiredError:
        raise HTTPException(
            status_code=403,
            detail="Este curso requiere un pago aprobado antes de inscribirte.",
        )

    return {
        "status": "success",
        "message": (
            f"Estudiante '{full_name}' "
            f"inscrito correctamente en '{course.title}'."
        ),
        "course": course.get_details(),
    }


# ============================================================
# BRIDGE + COMPOSITE: AGREGAR CONTENIDO AL CURSO (dueño o admin)
# ============================================================

@router.post(
    "/{course_id}/content/lessons",
    status_code=201,
)
def add_lesson(
    course_id: str,
    dto: LessonCreateDTO,
    user=Depends(require_staff),
):
    course = _get_course_or_404(course_id)
    _ensure_owner(course, user)

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
    lesson_types = {
        "video": VideoLesson,
        "quiz": InteractiveQuizLesson,
        "interactive_quiz": InteractiveQuizLesson,
    }
    lesson_class = lesson_types.get(dto.lesson_type.lower())

    if lesson_class is None:
        raise HTTPException(
            status_code=400,
            detail="Tipo de lección no válido. Usa 'video' o 'quiz'.",
        )

    extra = {}
    if dto.duration_minutes is not None:
        extra["duration_minutes"] = dto.duration_minutes

    lesson = lesson_class(
        dto.title,
        dto.media_id,
        provider,
        **extra,
    )

    # COMPOSITE: se incorpora la lección a la estructura de contenido.
    course.content.add_lesson(
        dto.module_title,
        lesson,
    )

    return {
        "message": "Lección agregada correctamente",
        "course_id": course.course_id,
        "lesson_id": lesson.lesson_id,
        "content": course.content.to_dict(),
    }


# ============================================================
# PROXY: CONTENIDO PROTEGIDO DEL CURSO
# ============================================================

def _content_proxy(course, user) -> ProtectedContentProxy:
    """
    Política de acceso al contenido (PROXY) de /content y /content/summary:
    cursos premium o de pago exigen inscripción (que a su vez exige pago);
    el dueño del curso y los administradores siempre pasan.
    """
    is_paid = course_requires_payment(course)
    is_owner_or_admin = (
        user.role == "admin" or course.instructor_id == user.id
    )

    return ProtectedContentProxy(
        real_factory=lambda: course.content,
        course=course,
        student_id=user.id,   # identidad por user_id (no por nombre)
        policy=EnrolledStudentPolicy(),
        requires_access=is_paid and not is_owner_or_admin,
    )


def _progress_proxy(course, user) -> ProtectedContentProxy:
    """
    Política de PROGRESO (completar lección y ver progreso): exige estar
    inscrito en TODOS los cursos, también en los gratuitos; el dueño y los
    administradores siempre pasan. Así el progreso solo existe para
    matrículas reales (y alimenta bien las recomendaciones).
    """
    is_owner_or_admin = (
        user.role == "admin" or course.instructor_id == user.id
    )
    return ProtectedContentProxy(
        real_factory=lambda: course.content,
        course=course,
        student_id=user.id,
        policy=EnrolledStudentPolicy(),
        requires_access=not is_owner_or_admin,
        # También aplica a cursos gratuitos: el mensaje no habla de "Premium".
        denied_message="Debes estar inscrito en el curso para ver o registrar tu progreso.",
    )


@router.get("/{course_id}/content")
def get_course_content(
    course_id: str,
    user=Depends(get_current_user),
):
    course = _get_course_or_404(course_id)
    proxy = _content_proxy(course, user)

    try:
        return proxy.to_dict()
    except ContentAccessDenied as error:
        raise HTTPException(status_code=403, detail=str(error))


# ============================================================
# VISITOR: PROGRESO Y RESUMEN DEL CONTENIDO
# ============================================================

def get_complete_lesson_use_case() -> CompleteLessonUseCase:
    # El composition root inyecta el bus único y la fábrica del evento
    # LESSON_COMPLETED (payload: lesson_id, progress_percent).
    return container.make_complete_lesson_use_case()


def get_progress_use_case() -> GetProgressUseCase:
    return container.make_progress_use_case()


@router.post("/{course_id}/lessons/{lesson_id}/complete")
def complete_lesson(
    course_id: str,
    lesson_id: str,
    user=Depends(get_current_user),
    use_case: CompleteLessonUseCase = Depends(get_complete_lesson_use_case),
):
    course = _get_course_or_404(course_id)
    try:
        result = use_case.execute(
            _progress_proxy(course, user), user.id, course.course_id, lesson_id
        )
    except ContentAccessDenied as error:
        raise HTTPException(status_code=403, detail=str(error))
    except LessonNotFoundError:
        raise HTTPException(status_code=404, detail="Lección no encontrada")

    return {"course_id": course.course_id, **result}


@router.get("/{course_id}/progress/me")
def get_my_progress(
    course_id: str,
    user=Depends(get_current_user),
    use_case: GetProgressUseCase = Depends(get_progress_use_case),
):
    course = _get_course_or_404(course_id)
    try:
        progress = use_case.execute(
            _progress_proxy(course, user), user.id, course.course_id
        )
    except ContentAccessDenied as error:
        raise HTTPException(status_code=403, detail=str(error))

    return {"course_id": course.course_id, "user_id": user.id, **progress}


@router.get("/{course_id}/content/summary")
def get_content_summary(
    course_id: str,
    user=Depends(get_current_user),
):
    course = _get_course_or_404(course_id)
    proxy = _content_proxy(course, user)
    summary = ContentSummaryVisitor()
    syllabus = ExportSyllabusVisitor()
    try:
        proxy.accept(summary)
        proxy.accept(syllabus)
    except ContentAccessDenied as error:
        raise HTTPException(status_code=403, detail=str(error))

    return {
        "course_id": course.course_id,
        **summary.result(),
        "syllabus_markdown": syllabus.to_markdown(),
    }

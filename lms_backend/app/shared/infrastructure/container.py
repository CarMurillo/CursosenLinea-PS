"""
Composition root ÚNICO de la aplicación: crea TODAS las instancias
compartidas (repositorios en memoria, fachada de cursos, adaptadores) y el
ÚNICO bus de eventos, lo cablea con sus observadores y expone fábricas
`make_*` que los routers usan como dependencias de FastAPI.

Ningún otro módulo crea repositorios globales ni buses: los módulos de
infraestructura solo definen las clases. Instancias:
`course_repository`, `payment_repository`, `progress_repository`,
`notification_repository`, `audit_log_repository`,
`learning_profile_repository`, `assessment_repository`,
`live_session_repository`, `certificate_repository`, `course_facade`,
`event_bus`.

- LESSON_COMPLETED: `make_complete_lesson_use_case()` inyecta el bus y
  `lesson_completed_event` como `event_factory`.
- Recomendaciones: `make_recommendations_use_case()` (perfil + catálogo +
  progreso calculado con ProgressVisitor).

Las capas de dominio/aplicación no conocen este módulo: reciben sus
dependencias (repositorios, bus, puertos) por constructor. Solo la capa de
infraestructura (routers FastAPI) importa de aquí.

Mapa de suscripciones (evento -> observadores):
- todos                    -> AuditLogObserver
- STUDENT_ENROLLED, PAYMENT_APPROVED, CERTIFICATE_ISSUED -> EmailNotificationObserver
- COURSE_PUBLISHED, STUDENT_ENROLLED, PAYMENT_APPROVED, ASSESSMENT_GRADED,
  CERTIFICATE_ISSUED, LIVE_SESSION_RECORDED -> InAppNotificationObserver
- PAYMENT_APPROVED         -> AutoEnrollOnPaymentObserver (publica STUDENT_ENROLLED)
- ASSESSMENT_GRADED        -> CertificateIssuerObserver (publica CERTIFICATE_ISSUED)
- STUDENT_ENROLLED, LESSON_COMPLETED, ASSESSMENT_GRADED, CERTIFICATE_ISSUED
                           -> RecommendationProfileObserver

Patrón State (fase patron-state): servicios de evaluaciones
(`make_assessment_service`), clases en vivo (`make_live_session_service`,
con el `JitsiAdapter` simulado) y certificados (`certificate_service`, que es
el `CertificateIssuerPort` real del observer). Todos usan el bus único.
"""

from typing import List, Optional

from app.modules.assessments.application.use_cases import AssessmentService
from app.modules.assessments.infrastructure.repository import (
    InMemoryAssessmentRepository,
)
from app.modules.certificates.application.observers import CertificateIssuerObserver
from app.modules.certificates.application.services import CertificateService
from app.modules.certificates.domain.ports import CertificateIssuerPort
from app.modules.certificates.infrastructure.repository import (
    InMemoryCertificateRepository,
)
from app.modules.courses.application.observers import AutoEnrollOnPaymentObserver
from app.modules.courses.application.use_cases import (
    EnrollStudentUseCase,
    course_requires_payment,
)
from app.modules.courses.domain.ports import CourseRepository
from app.modules.courses.application.course_facade import CourseFacade
from app.modules.courses.domain.visitor import ProgressVisitor
from app.modules.courses.infrastructure.repository import InMemoryCourseRepository
from app.modules.notifications.application.observers import InAppNotificationObserver
from app.modules.notifications.domain.ports import (
    AuditLogRepository,
    NotificationRepository,
)
from app.modules.notifications.infrastructure.repository import (
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
)
from app.modules.payments.application.use_cases import ProcessPaymentUseCase
from app.modules.payments.domain.ports import (
    CoursePurchaseInfo,
    CoursePurchaseReaderPort,
    PaymentRepository,
)
from app.modules.payments.infrastructure.repository import InMemoryPaymentRepository
from app.modules.progress.application.use_cases import (
    CompleteLessonUseCase,
    GetProgressUseCase,
)
from app.modules.progress.domain.ports import ProgressRepository
from app.modules.progress.infrastructure.repository import InMemoryProgressRepository
from app.modules.recommendations.application.observers import (
    RecommendationProfileObserver,
)
from app.modules.recommendations.application.use_cases import (
    GetRecommendationsUseCase,
)
from app.modules.recommendations.domain.models import CourseSnapshot
from app.modules.recommendations.domain.ports import LearningProfilePort
from app.modules.recommendations.infrastructure.repository import (
    InMemoryLearningProfileRepository,
)
from app.modules.live_sessions.application.use_cases import LiveSessionService
from app.modules.live_sessions.infrastructure.jitsi_adapter import JitsiAdapter
from app.modules.live_sessions.infrastructure.repository import (
    InMemoryLiveSessionRepository,
)
from app.shared.domain.events import DomainEvent, EventType, Subject
from app.shared.domain.state import CourseInfo
from app.shared.domain.observers import AuditLogObserver, EmailNotificationObserver

# ------------------------------------------------------------ repositorios
course_repository = InMemoryCourseRepository()
payment_repository = InMemoryPaymentRepository()
progress_repository = InMemoryProgressRepository()
notification_repository = InMemoryNotificationRepository()
audit_log_repository = InMemoryAuditLogRepository()
learning_profile_repository = InMemoryLearningProfileRepository()
assessment_repository = InMemoryAssessmentRepository()
live_session_repository = InMemoryLiveSessionRepository()
certificate_repository = InMemoryCertificateRepository()
video_conference = JitsiAdapter()                         # Adapter simulado


# ------------------------------------------------------------- adaptadores
def make_course_price_lookup(courses: CourseRepository):
    def lookup(course_id: str) -> Optional[float]:
        course = courses.get_by_id(course_id)
        return None if course is None else float(course.price or 0)
    return lookup


class CoursePurchaseReaderAdapter(CoursePurchaseReaderPort):
    """Adapta `CourseRepository` al puerto de lectura que usa pagos."""

    def __init__(self, courses: CourseRepository):
        self._courses = courses

    def get_purchase_info(self, course_id: str) -> Optional[CoursePurchaseInfo]:
        course = self._courses.get_by_id(course_id)
        if course is None:
            return None
        return CoursePurchaseInfo(
            course_id=course.course_id,
            owner_id=course.instructor_id,
            requires_payment=course_requires_payment(course),
            price=float(course.price or 0),
        )

    def is_enrolled(self, user_id: str, course_id: str) -> bool:
        course = self._courses.get_by_id(course_id)
        return course is not None and user_id in course.enrolled_students


def make_course_members_resolver(courses: CourseRepository):
    def members(course_id: str) -> List[str]:
        course = courses.get_by_id(course_id)
        return list(course.enrolled_students) if course is not None else []
    return members


class CourseCatalogAdapter:
    """Adapta `CourseRepository` al puerto `CourseCatalogPort` que usan
    evaluaciones, clases en vivo y certificados."""

    def __init__(self, courses: CourseRepository):
        self._courses = courses

    def get_course_info(self, course_id: str) -> Optional[CourseInfo]:
        course = self._courses.get_by_id(course_id)
        if course is None:
            return None
        details = course.get_details()
        return CourseInfo(
            course_id=course.course_id,
            title=course.title,
            instructor_id=course.instructor_id,
            enrolled_students=frozenset(course.enrolled_students),
            has_certificate=bool(details.get("certificate")),
        )


course_catalog = CourseCatalogAdapter(course_repository)
# Emisor real de certificados (CertificateIssuerPort del observer).
certificate_issuer = CertificateService(certificate_repository, course_catalog)


# --------------------------------------------------------------------- bus
def wire_event_bus(
    bus: Subject,
    *,
    courses: CourseRepository,
    payments: PaymentRepository,
    notifications: NotificationRepository,
    audit_log: AuditLogRepository,
    certificates: CertificateIssuerPort,
    profiles: LearningProfilePort,
) -> Subject:
    """Adjunta los observadores por defecto al bus dado (idempotente: limpia
    antes). Los observadores con dependencias las reciben por constructor."""
    bus.clear()

    bus.attach(AuditLogObserver(audit_log))  # sin filtro: todos los eventos
    bus.attach(
        EmailNotificationObserver(),
        EmailNotificationObserver.subscribed_events(),
    )
    bus.attach(
        InAppNotificationObserver(
            notifications, course_members=make_course_members_resolver(courses)
        ),
        InAppNotificationObserver.subscribed_events(),
    )

    # La inscripción automática usa un caso de uso conectado al MISMO bus,
    # así publica STUDENT_ENROLLED (evento encadenado).
    enroll = EnrollStudentUseCase(courses, payment_checker=payments, event_bus=bus)
    bus.attach(
        AutoEnrollOnPaymentObserver(enroll.execute),
        AutoEnrollOnPaymentObserver.subscribed_events(),
    )
    bus.attach(
        CertificateIssuerObserver(certificates, publisher=bus),
        CertificateIssuerObserver.subscribed_events(),
    )
    bus.attach(
        RecommendationProfileObserver(profiles),
        RecommendationProfileObserver.subscribed_events(),
    )
    return bus


def build_event_bus(
    *,
    courses: CourseRepository = course_repository,
    payments: PaymentRepository = payment_repository,
    notifications: NotificationRepository = notification_repository,
    audit_log: AuditLogRepository = audit_log_repository,
    certificates: CertificateIssuerPort = certificate_issuer,
    profiles: LearningProfilePort = learning_profile_repository,
) -> Subject:
    """Crea un bus nuevo y cableado. La app usa UNA sola instancia
    (`event_bus`, abajo); llámala directamente solo en pruebas aisladas."""
    return wire_event_bus(
        Subject(),
        courses=courses,
        payments=payments,
        notifications=notifications,
        audit_log=audit_log,
        certificates=certificates,
        profiles=profiles,
    )


# Bus ÚNICO compartido por toda la aplicación.
event_bus: Subject = build_event_bus()

# FACADE de cursos (única instancia): repositorio, verificador de pagos y bus.
course_facade = CourseFacade(
    course_repository,
    payment_checker=payment_repository,
    event_bus=event_bus,
)


# ------------------------------------------------------- progreso (Visitor)
def lesson_completed_event(
    *, user_id: str, course_id: str, lesson_id: str, progress: dict
) -> DomainEvent:
    """`event_factory` de CompleteLessonUseCase -> LESSON_COMPLETED."""
    return DomainEvent(
        EventType.LESSON_COMPLETED,
        user_id=user_id,
        course_id=course_id,
        payload={
            "lesson_id": lesson_id,
            "progress_percent": progress.get("percentage", 0.0),
        },
    )


def make_complete_lesson_use_case() -> CompleteLessonUseCase:
    return CompleteLessonUseCase(
        progress_repository,
        event_bus=event_bus,
        event_factory=lesson_completed_event,
    )


def make_progress_use_case() -> GetProgressUseCase:
    return GetProgressUseCase(progress_repository)


# ----------------------------------------------------------- recomendaciones
class RecommendationCatalogAdapter:
    """Adapta `CourseRepository` a `RecommendationCatalogPort`."""

    def __init__(self, courses: CourseRepository):
        self._courses = courses

    def list_snapshots(self) -> List[CourseSnapshot]:
        snapshots = []
        for course in self._courses.list_all():
            details = course.get_details()
            snapshots.append(CourseSnapshot(
                course_id=course.course_id,
                title=course.title,
                instructor=course.instructor or "",
                instructor_id=course.instructor_id,
                course_type=str(details.get("type") or ""),
                price=float(course.price or 0),
                premium=bool(details.get("premium")),
                has_certificate=bool(details.get("certificate")),
                enrolled_count=len(course.enrolled_students),
            ))
        return snapshots

    def enrolled_course_ids(self, user_id: str) -> List[str]:
        return [
            c.course_id for c in self._courses.list_all()
            if user_id in c.enrolled_students
        ]


class VisitorProgressReader:
    """`ProgressReaderPort`: % de avance con ProgressVisitor sobre el Composite."""

    def __init__(self, courses: CourseRepository, progress: ProgressRepository):
        self._courses = courses
        self._progress = progress

    def progress_percent(self, user_id: str, course_id: str) -> float:
        course = self._courses.get_by_id(course_id)
        if course is None:
            return 0.0
        visitor = ProgressVisitor(self._progress.completed_lessons(user_id, course_id))
        course.content.accept(visitor)
        return visitor.percentage


def make_recommendations_use_case() -> GetRecommendationsUseCase:
    return GetRecommendationsUseCase(
        learning_profile_repository,
        RecommendationCatalogAdapter(course_repository),
        VisitorProgressReader(course_repository, progress_repository),
    )


# ----------------------------------------------------------- casos de uso
def make_process_payment_use_case() -> ProcessPaymentUseCase:
    return ProcessPaymentUseCase(
        payment_repository,
        event_bus=event_bus,
        price_lookup=make_course_price_lookup(course_repository),
        course_reader=CoursePurchaseReaderAdapter(course_repository),
    )


def make_assessment_service() -> AssessmentService:
    return AssessmentService(assessment_repository, course_catalog, event_bus=event_bus)


def make_live_session_service() -> LiveSessionService:
    return LiveSessionService(
        live_session_repository, course_catalog, video_conference, event_bus=event_bus
    )


def make_certificate_service() -> CertificateService:
    return certificate_issuer


# ------------------------------------------------------------ observabilidad
def stats() -> dict:
    """Contadores básicos para GET /health (estado en memoria)."""
    courses = course_repository.list_all()
    return {
        "courses": len(courses),
        "enrollments": sum(len(c.enrolled_students) for c in courses),
        "payments": payment_repository.count(),
        "assessments": assessment_repository.count(),
        "live_sessions": live_session_repository.count(),
        "certificates": certificate_repository.count(),
        "notifications": notification_repository.count(),
        "audit_events": audit_log_repository.count(),
        "event_observers": len(event_bus.observers),
    }


# ----------------------------------------------------------------- pruebas
def reset_state() -> None:
    """Vacía los repositorios en memoria de este contenedor y re-cablea el
    bus con sus observadores por defecto (misma instancia de bus)."""
    course_repository.clear()
    payment_repository.clear()
    progress_repository.clear()
    notification_repository.clear()
    audit_log_repository.clear()
    certificate_repository.clear()
    learning_profile_repository.clear()
    assessment_repository.clear()
    live_session_repository.clear()
    video_conference.clear()
    wire_event_bus(
        event_bus,
        courses=course_repository,
        payments=payment_repository,
        notifications=notification_repository,
        audit_log=audit_log_repository,
        certificates=certificate_issuer,
        profiles=learning_profile_repository,
    )

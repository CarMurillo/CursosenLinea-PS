"""
Composition root (inicial): crea las instancias compartidas y el ÚNICO bus
de eventos de la aplicación, y lo cablea con sus observadores.

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
"""

from typing import List, Optional

from app.modules.certificates.application.observers import CertificateIssuerObserver
from app.modules.certificates.domain.ports import CertificateIssuerPort
from app.modules.certificates.infrastructure.stub import InMemoryCertificateIssuer
from app.modules.courses.application.observers import AutoEnrollOnPaymentObserver
from app.modules.courses.application.use_cases import EnrollStudentUseCase
from app.modules.courses.domain.ports import CourseRepository
from app.modules.courses.infrastructure.repository import course_repository
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
from app.modules.payments.domain.ports import PaymentRepository
from app.modules.payments.infrastructure.repository import payment_repository
from app.modules.recommendations.application.observers import (
    RecommendationProfileObserver,
)
from app.modules.recommendations.domain.ports import LearningProfilePort
from app.modules.recommendations.infrastructure.repository import (
    InMemoryLearningProfileRepository,
)
from app.shared.domain.events import Subject
from app.shared.domain.observers import AuditLogObserver, EmailNotificationObserver

# ------------------------------------------------------------ repositorios
notification_repository = InMemoryNotificationRepository()
audit_log_repository = InMemoryAuditLogRepository()
certificate_issuer = InMemoryCertificateIssuer()          # stub (fase State)
learning_profile_repository = InMemoryLearningProfileRepository()


# ------------------------------------------------------------- adaptadores
def make_course_price_lookup(courses: CourseRepository):
    def lookup(course_id: str) -> Optional[float]:
        course = courses.get_by_id(course_id)
        return None if course is None else float(course.price or 0)
    return lookup


def make_course_members_resolver(courses: CourseRepository):
    def members(course_id: str) -> List[str]:
        course = courses.get_by_id(course_id)
        return list(course.enrolled_students) if course is not None else []
    return members


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


# ----------------------------------------------------------- casos de uso
def make_process_payment_use_case() -> ProcessPaymentUseCase:
    return ProcessPaymentUseCase(
        payment_repository,
        event_bus=event_bus,
        price_lookup=make_course_price_lookup(course_repository),
    )


# ----------------------------------------------------------------- pruebas
def reset_state() -> None:
    """Vacía los repositorios en memoria de este contenedor y re-cablea el
    bus con sus observadores por defecto (misma instancia de bus)."""
    notification_repository.clear()
    audit_log_repository.clear()
    certificate_issuer.clear()
    learning_profile_repository.clear()
    wire_event_bus(
        event_bus,
        courses=course_repository,
        payments=payment_repository,
        notifications=notification_repository,
        audit_log=audit_log_repository,
        certificates=certificate_issuer,
        profiles=learning_profile_repository,
    )

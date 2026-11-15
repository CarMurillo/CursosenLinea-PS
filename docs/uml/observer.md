# Observer: diagrama de clases

Fuente: `app/shared/domain/events.py`, `app/shared/domain/observers.py`,
`app/modules/*/application/observers.py` y el cableado en `app/shared/infrastructure/container.py`
(`wire_event_bus`). Se muestran solo los métodos relevantes al patrón.

```mermaid
classDiagram
    direction LR

    class EventType {
        <<enumeration>>
        COURSE_PUBLISHED
        STUDENT_ENROLLED
        PAYMENT_APPROVED
        LESSON_COMPLETED
        ASSESSMENT_SUBMITTED
        ASSESSMENT_GRADED
        CERTIFICATE_ISSUED
        LIVE_SESSION_RECORDED
    }

    class DomainEvent {
        <<frozen dataclass>>
        +event_type: EventType
        +user_id: str
        +course_id: str
        +payload: Mapping
        +occurred_at: datetime
        +event_id: str
        +to_dict() dict
    }

    class EventPublisher {
        <<Protocol>>
        +notify(event)
    }

    class Subject {
        -_subscriptions: list
        -_max_depth: int = 8
        +attach(observer, event_types=None)
        +detach(observer)
        +notify(event)
        +publish(event)
        +clear()
        +observers: list
    }

    class Observer {
        <<abstract>>
        +update(event)*
    }

    class AuditLogObserver {
        +update(event)
    }
    class EmailNotificationObserver {
        +sent: list
        +subscribed_events()
        +update(event)
    }
    class InAppNotificationObserver {
        +subscribed_events()
        +update(event)
    }
    class AutoEnrollOnPaymentObserver {
        +subscribed_events()
        +update(event)
    }
    class CertificateIssuerObserver {
        +subscribed_events()
        +update(event)
    }
    class RecommendationProfileObserver {
        +subscribed_events()
        +update(event)
    }

    class AuditLogRepository {
        <<abstract>>
    }
    class NotificationRepository {
        <<abstract>>
    }
    class CertificateIssuerPort {
        <<Protocol>>
    }
    class LearningProfilePort {
        <<Protocol>>
    }
    class EnrollStudentUseCase {
        +execute(course_id, user_id, student_name)
    }

    EventPublisher <|.. Subject
    Subject o--> "0..*" Observer : suscripciones
    Subject ..> DomainEvent : difunde
    DomainEvent --> EventType

    Observer <|-- AuditLogObserver
    Observer <|-- EmailNotificationObserver
    Observer <|-- InAppNotificationObserver
    Observer <|-- AutoEnrollOnPaymentObserver
    Observer <|-- CertificateIssuerObserver
    Observer <|-- RecommendationProfileObserver

    AuditLogObserver --> AuditLogRepository
    InAppNotificationObserver --> NotificationRepository
    AutoEnrollOnPaymentObserver --> EnrollStudentUseCase : enroll.execute
    EnrollStudentUseCase --> Subject : publica STUDENT_ENROLLED
    CertificateIssuerObserver --> CertificateIssuerPort
    CertificateIssuerObserver --> Subject : publica CERTIFICATE_ISSUED
    RecommendationProfileObserver --> LearningProfilePort
```

## Suscripciones (según `wire_event_bus`)

| Observador | Eventos |
|---|---|
| `AuditLogObserver` | todos (sin filtro) |
| `EmailNotificationObserver` | `STUDENT_ENROLLED`, `PAYMENT_APPROVED`, `CERTIFICATE_ISSUED` |
| `InAppNotificationObserver` | `COURSE_PUBLISHED`, `STUDENT_ENROLLED`, `PAYMENT_APPROVED`, `ASSESSMENT_GRADED`, `CERTIFICATE_ISSUED`, `LIVE_SESSION_RECORDED` |
| `AutoEnrollOnPaymentObserver` | `PAYMENT_APPROVED` |
| `CertificateIssuerObserver` | `ASSESSMENT_GRADED` (solo si `payload.passed`) |
| `RecommendationProfileObserver` | `STUDENT_ENROLLED`, `LESSON_COMPLETED`, `ASSESSMENT_GRADED`, `CERTIFICATE_ISSUED` |

`LIVE_SESSION_RECORDED` se notifica in-app al instructor y a los inscritos del curso **en ese momento**
(`_COURSE_WIDE` en `InAppNotificationObserver`).

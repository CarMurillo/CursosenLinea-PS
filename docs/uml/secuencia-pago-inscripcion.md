# Secuencia: pago → PAYMENT_APPROVED → auto-inscripción → STUDENT_ENROLLED

Fuente: `app/modules/payments/infrastructure/api.py`, `ProcessPaymentUseCase`
(`app/modules/payments/application/use_cases.py`), `Subject.notify` (`app/shared/domain/events.py`),
`AutoEnrollOnPaymentObserver` (`app/modules/courses/application/observers.py`),
`EnrollStudentUseCase` (`app/modules/courses/application/use_cases.py`) y el cableado de
`wire_event_bus` (`app/shared/infrastructure/container.py`).

Todo ocurre **en la misma petición HTTP y en el mismo hilo** (bus síncrono en memoria). El orden de
los observadores es el orden de `attach` en `wire_event_bus`: auditoría, correo, in-app,
auto-inscripción, certificados, recomendaciones (cada uno filtra por tipo de evento).

```mermaid
sequenceDiagram
    autonumber
    actor E as Estudiante (frontend)
    participant API as POST /payments/process
    participant UC as ProcessPaymentUseCase
    participant GW as StripePaymentAdapter / WompiPaymentAdapter (simulado)
    participant PR as InMemoryPaymentRepository
    participant BUS as Subject (event_bus único)
    participant AUD as AuditLogObserver
    participant MAIL as EmailNotificationObserver
    participant INAPP as InAppNotificationObserver
    participant AUTO as AutoEnrollOnPaymentObserver
    participant ENR as EnrollStudentUseCase
    participant CR as InMemoryCourseRepository
    participant REC as RecommendationProfileObserver

    E->>API: {amount, currency, gateway, course_id} + Bearer token
    API->>UC: execute(dto, user_id, customer_email)
    UC->>PR: has_approved_payment(user_id, course_id)
    alt ya pagado
        UC-->>API: AlreadyPaidError
        API-->>E: 409
    end
    UC->>UC: price_lookup(course_id), amount >= price
    alt monto menor que el precio
        UC-->>API: AmountBelowPriceError
        API-->>E: 400
    end
    UC->>GW: process_payment(amount, currency, customer_email)
    GW-->>UC: PaymentResult
    UC->>PR: save(Payment)
    alt rechazado
        UC-->>API: PaymentRejectedError
        API-->>E: 400 (no se publica evento)
    end

    UC->>BUS: notify(PAYMENT_APPROVED)
    BUS->>AUD: update (registra en audit log)
    BUS->>MAIL: update (print "Enviando correo a ...")
    BUS->>INAPP: update (notificación "pago aprobado" al estudiante)
    BUS->>AUTO: update(PAYMENT_APPROVED)
    AUTO->>ENR: execute(course_id, user_id, customer_name)
    ENR->>CR: get_by_id(course_id)
    ENR->>PR: has_approved_payment (payment_checker)
    ENR->>ENR: course.enrolled_students.append(user_id)
    ENR->>BUS: notify(STUDENT_ENROLLED) [anidado, profundidad 2]
    BUS->>AUD: update (registra inscripción)
    BUS->>MAIL: update (correo de inscripción)
    BUS->>INAPP: update (notificación de inscripción)
    BUS->>REC: update (perfil: curso inscrito)
    BUS-->>ENR: fin difusión anidada
    ENR-->>AUTO: Course
    BUS-->>UC: fin difusión PAYMENT_APPROVED
    UC-->>API: Payment (approved)
    API-->>E: 200 {success, payment_id, status:"approved", ...}

    Note over E,CR: Después: GET /courses/{id}/content pasa el Proxy (inscrito) → 200.<br/>GET /notifications/me y GET /admin/audit-log muestran ambos eventos.
```

## Notas

- Un observador que lanza excepción se registra con `logging` y no detiene a los demás ni al pago
  (`Subject.notify`). Si la inscripción automática falla, el pago queda aprobado igualmente.
  `AutoEnrollOnPaymentObserver` además captura `AlreadyEnrolledError` y `CourseNotFoundError` y solo
  los registra en el log.
- Guardas contra bucles: un observador no recibe otro evento del mismo tipo mientras procesa uno, y la
  cadena anidada se corta en `max_depth = 8`.
- Pruebas que cubren este flujo: `test_observer.py::test_encadenado_legitimo_pago_a_inscripcion`,
  `test_observer.py::test_api_pago_inscribe_automaticamente`,
  `test_correcciones.py::test_pago_luego_inscripcion_y_contenido`, `test_flow_e2e.py::test_flujo_completo_de_la_demo`.

## Continuación: contenido → lección → evaluación → certificado

Fuente: `app/modules/courses/infrastructure/api.py` (Proxy y progreso), `CompleteLessonUseCase`,
`AssessmentService.submit_attempt`, `CertificateIssuerObserver` y `CertificateService.issue`.

```mermaid
sequenceDiagram
    autonumber
    actor E as Estudiante inscrito
    participant C as API de cursos
    participant PX as ProtectedContentProxy
    participant CL as CompleteLessonUseCase
    participant AS as AssessmentService
    participant A as Assessment (PublishedState)
    participant BUS as Subject (event_bus)
    participant CERT as CertificateIssuerObserver
    participant CS as CertificateService

    E->>C: GET /courses/{id}/content
    C->>PX: to_dict()
    PX->>PX: EnrolledStudentPolicy.can_access(user_id, course)
    PX-->>E: 200 árbol de contenido (403 si no hay acceso)

    E->>C: POST /courses/{id}/lessons/{lesson_id}/complete
    C->>CL: execute(proxy, user_id, course_id, lesson_id)
    CL->>PX: accept(ProgressVisitor / LessonIndexVisitor)
    CL->>BUS: notify(LESSON_COMPLETED) [solo la primera vez]
    CL-->>E: {already_completed, progress}

    E->>AS: POST /assessments/{assessment_id}/attempts {answers}
    AS->>A: submit_attempt(user_id, answers)
    A->>A: estado.submit_attempt → _grade_and_record
    A-->>AS: Attempt (score, percentage, passed)
    AS->>BUS: notify(ASSESSMENT_SUBMITTED)
    AS->>BUS: notify(ASSESSMENT_GRADED)
    BUS->>CERT: update (si passed)
    CERT->>CS: issue(user_id, course_id, payload)
    CS-->>CERT: certificado o None (curso sin certificado / ya emitido)
    CERT->>BUS: notify(CERTIFICATE_ISSUED) [solo si se emitió]
    AS-->>E: 201 Attempt

    E->>C: GET /certificates/me
```

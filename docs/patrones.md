# Patrones de diseño GoF en el LMS

Este documento describe **solo lo que existe en el código** de la rama
`feature/patrones-observer-state-visitor`. Todas las rutas de archivo son relativas a
`lms_backend/` y todas las pruebas están en `lms_backend/tests/`.

- Swagger: `http://127.0.0.1:8000/docs` (con el backend arriba).
- Datos de demostración: `python scripts/seed.py` (ver `README.md` raíz).
- Para endpoints protegidos: `POST /auth/login`, copiar `access_token` y pulsar **Authorize**
  en Swagger. El esquema es `Bearer <token>`; en el cuadro se pega solo el token.
- Diagramas: [`docs/uml/`](uml/). Decisiones: [`docs/adr/`](adr/).

## Tabla resumen

| Patrón | Clases reales | Archivo | Endpoint | Pruebas |
|---|---|---|---|---|
| Singleton | `SystemConfig` | `app/shared/infrastructure/config/system_config.py` | indirecto: `GET /health` (app, versión) | `test_singleton.py`, `test_correcciones.py::test_b5_bd_usa_system_config` |
| Factory Method | `CourseFactory.create_course` → `VideoCourse`, `LiveClassCourse` | `app/modules/courses/domain/models.py` | `POST /courses/` (`course_type`) | `test_courses_api.py::test_publish_video_course_uses_factory_method`, `::test_publish_live_course_uses_factory_method` |
| Abstract Factory | `UserFactory`, `StudentFactory`, `InstructorFactory`, `AdminFactory`, `UserCreationService` | `app/modules/auth/domain/factories.py` | `POST /auth/register` | `test_users.py` |
| Builder | `CourseBuilder` | `app/modules/courses/domain/builder.py` | `POST /courses/` | `test_courses_patterns.py::test_builder_*` |
| Prototype | `Course.clone()`, `CloneCourseUseCase` | `app/modules/courses/domain/models.py`, `app/modules/courses/application/use_cases.py` | `POST /courses/{course_id}/clone` | `test_courses_patterns.py::test_prototype_clones_course`, `test_correcciones.py::test_b7_*` |
| Decorator | `CourseDecorator`, `PremiumCourseDecorator`, `CertificateCourseDecorator` | `app/modules/courses/domain/decorator.py` | `POST /courses/` (`premium`, `certificate`) | `test_correcciones.py::test_b7_clone_decorado_conserva_decoradores_e_id_nuevo`, `test_flow_e2e.py` |
| Adapter | `PaymentGatewayPort`, `StripePaymentAdapter`, `WompiPaymentAdapter`; `JitsiAdapter` | `app/modules/payments/domain/adapter.py`; `app/modules/live_sessions/infrastructure/jitsi_adapter.py` | `POST /payments/process`; `POST /live-sessions/{session_id}/end` | `test_payments.py`; `test_state.py::test_ciclo_completo_clase_en_vivo_con_url_de_grabacion` |
| Bridge | `LessonContent` (`VideoLesson`, `InteractiveQuizLesson`) × `MediaStorageProvider` (`VimeoStorageProvider`, `S3StorageProvider`) | `app/modules/courses/domain/bridge.py` | `POST /courses/{course_id}/content/lessons` (`lesson_type`, `provider`) | `test_correcciones.py::test_b8_*` |
| Composite | `ContentComponent`, `LessonModule`, `CourseContent` (hojas: lecciones del Bridge) | `app/modules/courses/domain/content_component.py`, `composite.py` | `POST /courses/{course_id}/content/lessons`, `GET /courses/{course_id}/content` | `test_visitor.py::test_summary_visitor_modulos_anidados_suman_duracion`, `::test_to_dict_y_render_siguen_funcionando` |
| Flyweight | `ContentMetadata`, `ContentMetadataFactory` | `app/modules/courses/domain/content_flyweight.py` | `GET /courses/content-metadata/{content_type}` | `test_new_patterns.py::test_flyweight_*`, `test_correcciones.py::test_e6_flyweight_compartido_tras_clone` |
| Proxy | `ProtectedContentProxy`, `EnrolledStudentPolicy`, `ContentAccessDenied` | `app/modules/courses/domain/content_proxy.py` | `GET /courses/{course_id}/content` (también `/content/summary`, progreso) | `test_new_patterns.py::test_proxy_*`, `test_visitor.py::test_proxy_bloquea_visitante_sin_acceso` |
| Facade | `CourseFacade(repository, payment_checker=None, event_bus=None)` | `app/modules/courses/application/course_facade.py` | `GET/POST /courses/`, `POST /courses/{course_id}/clone`, `POST /courses/{course_id}/enroll`, `GET /courses/me/enrolled` | `test_new_patterns.py::test_facade_cuatro_operaciones` |
| Observer | `EventType`, `DomainEvent`, `Observer`, `Subject` + 6 observadores | `app/shared/domain/events.py`, `app/shared/domain/observers.py`, `app/modules/*/application/observers.py` | `POST /payments/process`, `POST /courses/{course_id}/enroll`, `GET /notifications/me`, `GET /admin/audit-log` | `test_observer.py` |
| State | `Assessment` + `DraftState`/`PublishedState`/`ClosedState`; `LiveSession` + `ScheduledState`/`LiveState`/`EndedState`/`RecordedState` | `app/modules/assessments/domain/states.py`, `app/modules/live_sessions/domain/states.py` | `POST /assessments/{assessment_id}/publish`, `/close`, `/attempts`; `POST /live-sessions/{session_id}/start`, `/end` | `test_state.py` |
| Visitor | `ContentVisitor`, `DurationVisitor`, `ProgressVisitor`, `ContentSummaryVisitor`, `ExportSyllabusVisitor`, `LessonIndexVisitor` | `app/modules/courses/domain/visitor.py` | `GET /courses/{course_id}/content/summary`, `POST /courses/{course_id}/lessons/{lesson_id}/complete`, `GET /courses/{course_id}/progress/me` | `test_visitor.py` |

Fuera de los 15 patrones pedidos también existe un **Strategy** en recomendaciones
(`RecommendationRule` y sus reglas en `app/modules/recommendations/domain/strategies.py`,
probado en `test_recommendations.py::test_reglas_son_estrategias_intercambiables_y_hay_limite`).

---

## Creacionales

### Singleton

- **Problema en el LMS**: la configuración (nombre, versión, `DATABASE_URL`, orígenes CORS, nivel de
  log) debe leerse una vez y ser la misma para la API, la base de datos y la observabilidad.
- **Clases**: `SystemConfig` (`__new__` devuelve siempre `_instance`) y `get_system_config()`.
- **Archivo**: `app/shared/infrastructure/config/system_config.py`.
- **Uso real**: `app/main.py` (título, versión, CORS, logging), `app/shared/infrastructure/database.py`
  (`DATABASE_URL = SystemConfig().database_url`) y `GET /health` en
  `app/shared/infrastructure/observability.py`.
- **Pruebas**: `test_singleton.py::test_system_config_singleton`, `::test_system_config_properties`,
  `test_correcciones.py::test_b5_bd_usa_system_config`.
- **Swagger**: `GET /health` devuelve `app` y `version` tomados del Singleton. La identidad de la
  instancia se demuestra con las pruebas, no por HTTP.

### Factory Method

- **Problema**: crear el tipo de curso correcto (video bajo demanda o clase en vivo) sin que el caso de
  uso conozca las clases concretas.
- **Clases**: `CourseFactory.create_course(...)` (método estático) → `VideoCourse` o `LiveClassCourse`,
  ambos subclases de `Course`.
- **Archivo**: `app/modules/courses/domain/models.py`. Lo invoca `CourseBuilder.build()`.
- **Endpoint**: `POST /courses/` con `course_type: "video"` o `"live"` (rol instructor o admin).
- **Pruebas**: `test_courses_api.py::test_publish_video_course_uses_factory_method`,
  `::test_publish_live_course_uses_factory_method`.
- **Swagger**: iniciar sesión como `instructor@lms.demo`, `POST /courses/` con `course_type: "live"`;
  la respuesta trae `type: "Clase en Vivo (Videoconferencia)"`.

### Abstract Factory

- **Problema**: el registro crea usuarios de tres roles con atributos distintos (`Student`,
  `Instructor` con especialización, `Administrator` con permisos) sin `if/elif` en el caso de uso.
- **Clases**: `UserFactory` (ABC, `create_user(first_name, last_name, email, password_hash, **extra_fields)`),
  `StudentFactory`, `InstructorFactory`, `AdminFactory` y `UserCreationService.register_user(role, ...)`,
  que elige la fábrica por `Role`. Productos en `app/modules/auth/domain/models.py`
  (`User`, `Student`, `Instructor`, `Administrator`).
- **Archivo**: `app/modules/auth/domain/factories.py`. Lo usa `RegisterUserUseCase`
  (`app/modules/auth/application/use_cases.py`).
- **Endpoint**: `POST /auth/register` (solo `student` o `instructor`; `admin` responde 403).
- **Pruebas**: `test_users.py::test_create_student`, `::test_create_instructor`.
- **Swagger**: `POST /auth/register` con `role: "instructor"` y `specialization`; la respuesta trae
  `details` con la especialización.
- **Nota honesta**: cada fábrica concreta produce un único producto (el usuario del rol). No hay una
  familia de varios productos por rol. Por eso la implementación está más cerca de un conjunto de
  Factory Methods seleccionados por un servicio que de un Abstract Factory clásico.

### Builder

- **Problema**: armar un curso paso a paso, validando cada dato (título, instructor, precio ≥ 0, tipo)
  antes de crear el objeto.
- **Clases**: `CourseBuilder` (`set_title`, `set_instructor`, `set_price`, `set_course_type`, `build`).
  `build()` delega en `CourseFactory`.
- **Archivo**: `app/modules/courses/domain/builder.py`. Lo usa `PublishCourseUseCase`.
- **Endpoint**: `POST /courses/`. Con `price: -1` la validación responde 422.
- **Pruebas**: `test_courses_patterns.py::test_builder_creates_video_course`,
  `::test_builder_creates_live_course`, `::test_builder_rejects_negative_price`.

### Prototype

- **Problema**: un instructor quiere duplicar un curso (con su contenido y sus decoradores) para otro
  grupo sin reconstruirlo.
- **Clases**: `Course.clone()` (copia profunda con id nuevo y lista de inscritos vacía) y
  `CloneCourseUseCase`. El contenido del clon se renombra a `"Contenido de <nuevo título>"`.
- **Archivos**: `app/modules/courses/domain/models.py`, `app/modules/courses/application/use_cases.py`.
- **Endpoint**: `POST /courses/{course_id}/clone` con `{ "new_title": "..." }` (dueño o admin).
- **Pruebas**: `test_courses_patterns.py::test_prototype_clones_course`, `::test_clone_is_saved_in_repository`,
  `test_correcciones.py::test_b7_clone_renombra_raiz_composite`,
  `::test_b7_clone_decorado_conserva_decoradores_e_id_nuevo`, `test_visitor.py::test_clone_conserva_duracion_y_lesson_ids`.
- **Swagger**: clonar un curso del seed como `instructor@lms.demo`; el `id` cambia y `decorators` se conserva.

## Estructurales

### Decorator

- **Problema**: añadir características opcionales a un curso (premium con recargo, certificado) sin
  una subclase por combinación.
- **Clases**: `CourseDecorator` (ABC, envuelve un `Course`), `PremiumCourseDecorator`
  (`PREMIUM_SURCHARGE = 0.20`: `price` = base × 1.2, agrega `premium_benefits` y `base_price`) y
  `CertificateCourseDecorator`.
- **Archivo**: `app/modules/courses/domain/decorator.py`. Los aplica `PublishCourseUseCase`.
- **Endpoint**: `POST /courses/` con `premium: true` y/o `certificate: true`.
- **Pruebas**: `test_correcciones.py::test_b7_clone_decorado_conserva_decoradores_e_id_nuevo`;
  `test_flow_e2e.py::test_flujo_completo_de_la_demo` verifica el precio 49.9 × 1.2 = 59.88.
- **Swagger**: `POST /courses/` con `price: 49.9, premium: true, certificate: true`; respuesta con
  `price: 59.88` y `decorators: ["premium", "certificate"]`.

### Adapter

- **Problema**: las pasarelas de pago (y el proveedor de videoconferencia) tienen interfaces propias;
  el dominio necesita una sola.
- **Pagos**: puerto `PaymentGatewayPort`; `StripePaymentAdapter` adapta `StripeSDK` (monto en centavos)
  y `WompiPaymentAdapter` adapta `WompiSDK` (referencia propia); ambos devuelven `PaymentResult`.
  Los SDK son **simulados** (no hay red ni claves). Archivo `app/modules/payments/domain/adapter.py`.
  `ProcessPaymentUseCase` elige el adaptador por diccionario (`app/modules/payments/application/use_cases.py`).
- **Videoconferencia**: puerto `VideoConferencePort` (`app/modules/live_sessions/domain/ports.py`) y
  `JitsiAdapter` **simulado** (genera URL de sala y de grabación sin red) en
  `app/modules/live_sessions/infrastructure/jitsi_adapter.py`.
- **Adaptadores internos**: `CourseCatalogAdapter`, `RecommendationCatalogAdapter` y `VisitorProgressReader`
  en `app/shared/infrastructure/container.py` adaptan `CourseRepository` a los puertos de otros módulos.
- **Endpoints**: `POST /payments/process` (`gateway: "stripe" | "wompi"`), `GET /payments/me`;
  `POST /live-sessions/{session_id}/end`.
- **Pruebas**: `test_payments.py` (`test_stripe_adapter_traduce_a_centavos_y_normaliza_respuesta`,
  `test_wompi_adapter_usa_referencia_y_normaliza_respuesta`, `test_ambos_adaptadores_cumplen_el_mismo_puerto`, …),
  `test_correcciones.py::test_b1_*`.
- **Swagger**: como `estudiante@lms.demo`, `POST /payments/process` con el `price` del curso premium
  del seed y `gateway: "wompi"`; luego `GET /payments/me`.

### Bridge

- **Problema**: el tipo de lección (video, quiz) y el proveedor de medios (Vimeo, S3) varían de forma
  independiente; sin Bridge habría una clase por combinación.
- **Clases**: abstracción `LessonContent` (`VideoLesson`, `InteractiveQuizLesson`) e implementador
  `MediaStorageProvider` (`VimeoStorageProvider`, `S3StorageProvider`). Las lecciones tienen
  `lesson_id` y `duration_minutes` (por defecto 10).
- **Archivo**: `app/modules/courses/domain/bridge.py`. El endpoint elige ambas clases por diccionario
  en `app/modules/courses/infrastructure/api.py`.
- **Endpoint**: `POST /courses/{course_id}/content/lessons` con `lesson_type` (`video|quiz`) y
  `provider` (`vimeo|s3`).
- **Pruebas**: `test_correcciones.py::test_b8_leccion_tiene_id_y_duracion`, `::test_b8_endpoint_lessons_con_duracion`.
- **Swagger**: agregar una lección con `provider: "s3"` y otra con `"vimeo"`; el campo `url` de cada
  lección cambia según el proveedor.

### Composite

- **Problema**: el contenido de un curso es un árbol (curso → módulos → lecciones) que se debe tratar
  de forma uniforme para renderizarlo, serializarlo y recorrerlo.
- **Clases**: `ContentComponent` (ABC con `render_content`, `to_dict`, `accept`), `LessonModule`
  (compuesto: `add`, `remove`), `CourseContent` (raíz: `add_module`, `find_module`, `add_lesson`).
  Hojas: las lecciones del Bridge.
- **Archivos**: `app/modules/courses/domain/content_component.py`, `app/modules/courses/domain/composite.py`.
- **Endpoints**: `POST /courses/{course_id}/content/lessons` (agrega al árbol), `GET /courses/{course_id}/content`
  (devuelve `{title, items[]}` anidado).
- **Pruebas**: `test_visitor.py::test_summary_visitor_modulos_anidados_suman_duracion`,
  `::test_to_dict_y_render_siguen_funcionando`, `::test_find_module_sin_isinstance_ignora_lecciones`.

### Flyweight

- **Problema**: muchas lecciones comparten los mismos metadatos de tipo (etiqueta e icono); no tiene
  sentido duplicarlos.
- **Clases**: `ContentMetadata` (inmutable; `__copy__`/`__deepcopy__` devuelven la misma instancia) y
  `ContentMetadataFactory.get_metadata(content_type)` con caché y lock. Tipos: `video`, `quiz`, `document`.
- **Archivo**: `app/modules/courses/domain/content_flyweight.py`. Las lecciones obtienen su `metadata`
  de la fábrica (`bridge.py`). El progreso del estudiante es estado extrínseco (vive en `ProgressRepository`).
- **Endpoint**: `GET /courses/content-metadata/{content_type}` (público; tipo inválido → 400).
- **Pruebas**: `test_new_patterns.py::test_flyweight_reutiliza_metadatos`, `::test_flyweight_rechaza_tipo_desconocido`,
  `::test_flyweight_lecciones_comparten_metadatos`, `test_correcciones.py::test_e6_flyweight_compartido_tras_clone`.
- **Limitación**: no hay pruebas de carga ni medición de memoria; solo se verifica la identidad de instancias.

### Proxy

- **Problema**: el contenido de un curso premium o de pago solo debe entregarse a inscritos (y la
  inscripción exige pago aprobado). El dueño y el admin siempre pasan.
- **Clases**: `ProtectedContentProxy` (subclase de `ContentComponent`; carga perezosa del sujeto real
  mediante `real_factory`), `AccessPolicy` (Protocol), `EnrolledStudentPolicy` (compara por `user_id`),
  `ContentAccessDenied` (→ HTTP 403).
- **Archivo**: `app/modules/courses/domain/content_proxy.py`. Se construye en
  `_content_proxy()` y `_progress_proxy()` de `app/modules/courses/infrastructure/api.py`.
- **Endpoints**: `GET /courses/{course_id}/content`, `GET /courses/{course_id}/content/summary`
  (política de contenido); `POST /courses/{course_id}/lessons/{lesson_id}/complete` y
  `GET /courses/{course_id}/progress/me` (política de progreso: exige inscripción también en cursos gratuitos).
- **Pruebas**: `test_new_patterns.py::test_proxy_bloquea_premium_sin_inscripcion`,
  `::test_proxy_permite_inscrito_y_es_perezoso`, `::test_proxy_no_bloquea_no_premium`,
  `test_visitor.py::test_proxy_bloquea_visitante_sin_acceso`, `::test_proxy_delega_visitante_con_acceso`,
  `test_correcciones.py::test_b2_premium_sin_pago_403_y_no_inscribe`.
- **Swagger**: como `estudiante@lms.demo`, `GET /courses/{id}/content` del curso premium del seed → 403.
  Pagar con `POST /payments/process` y repetir → 200.

### Facade

- **Problema**: los endpoints de cursos no deben instanciar ni coordinar cada caso de uso.
- **Clase**: `CourseFacade(repository, payment_checker=None, event_bus=None)` con `list_courses`,
  `list_enrolled_courses`, `get_course`, `create_course`, `clone_course`, `enroll_student`.
  Depende del puerto `CourseRepository`. La instancia única `course_facade` se crea en
  `app/shared/infrastructure/container.py` con el repositorio, el repositorio de pagos y el bus.
- **Archivo**: `app/modules/courses/application/course_facade.py`.
- **Endpoints**: `GET /courses/`, `POST /courses/`, `GET /courses/me/enrolled`,
  `POST /courses/{course_id}/clone`, `POST /courses/{course_id}/enroll`.
- **Pruebas**: `test_new_patterns.py::test_facade_cuatro_operaciones` (crea `CourseFacade(repo, payment_checker=...)`).

## Comportamiento

### Observer

- **Problema**: varias reacciones a un mismo hecho (pago aprobado, inscripción, nota, grabación)
  sin que el caso de uso conozca a quién avisar.
- **Núcleo** (`app/shared/domain/events.py`): `EventType` (8 tipos), `DomainEvent` (dataclass `frozen`,
  `payload` de solo lectura), `Observer` (ABC con `update`), `Subject` (`attach(observer, event_types=None)`,
  `detach`, `notify`/`publish`, `clear`). Un observador que falla se registra con `logging` y no detiene
  a los demás. Guardas contra bucles: reentrada por (observador, tipo) y `max_depth = 8`.
- **Bus único**: `event_bus` en `app/shared/infrastructure/container.py`, cableado por `wire_event_bus()`.
- **Observadores y suscripciones reales**:

  | Observador | Archivo | Eventos |
  |---|---|---|
  | `AuditLogObserver` (alias `LoggingObserver`) | `app/shared/domain/observers.py` | todos |
  | `EmailNotificationObserver` (simulado: `print` + lista `sent`) | `app/shared/domain/observers.py` | `STUDENT_ENROLLED`, `PAYMENT_APPROVED`, `CERTIFICATE_ISSUED` |
  | `InAppNotificationObserver` | `app/modules/notifications/application/observers.py` | `COURSE_PUBLISHED`, `STUDENT_ENROLLED`, `PAYMENT_APPROVED`, `ASSESSMENT_GRADED`, `CERTIFICATE_ISSUED`, `LIVE_SESSION_RECORDED` |
  | `AutoEnrollOnPaymentObserver` | `app/modules/courses/application/observers.py` | `PAYMENT_APPROVED` (publica `STUDENT_ENROLLED`) |
  | `CertificateIssuerObserver` | `app/modules/certificates/application/observers.py` | `ASSESSMENT_GRADED` aprobado (publica `CERTIFICATE_ISSUED`) |
  | `RecommendationProfileObserver` | `app/modules/recommendations/application/observers.py` | `STUDENT_ENROLLED`, `LESSON_COMPLETED`, `ASSESSMENT_GRADED`, `CERTIFICATE_ISSUED` |

- **Publicadores**: `PublishCourseUseCase` (`COURSE_PUBLISHED`), `EnrollStudentUseCase` (`STUDENT_ENROLLED`),
  `ProcessPaymentUseCase` (`PAYMENT_APPROVED`), `CompleteLessonUseCase` (`LESSON_COMPLETED`, solo la
  primera vez), `AssessmentService` (`ASSESSMENT_SUBMITTED` y `ASSESSMENT_GRADED`),
  `LiveSessionService.end` (`LIVE_SESSION_RECORDED`), `CertificateIssuerObserver` (`CERTIFICATE_ISSUED`).
  `ASSESSMENT_SUBMITTED` solo lo recibe `AuditLogObserver`.
- **Endpoints para ver el efecto**: `POST /payments/process`, `POST /courses/{course_id}/enroll`,
  `GET /notifications/me`, `GET /admin/audit-log?event_type=payment_approved`, `GET /health` (`event_observers`).
- **Pruebas**: `test_observer.py` (attach/detach, filtro por tipo, observador que falla, encadenado
  sin bucle, pago → inscripción, nota → certificado, API de notificaciones y auditoría),
  `test_courses_api.py::test_enroll_student_notifies_observers`.
- **Swagger**: pagar como estudiante; luego `GET /notifications/me` (pago aprobado + inscripción) y,
  como `admin@lms.demo`, `GET /admin/audit-log` (`payment_approved` seguido de `student_enrolled`).
- **Diagramas**: [`uml/observer.md`](uml/observer.md), [`uml/secuencia-pago-inscripcion.md`](uml/secuencia-pago-inscripcion.md).

### State

- **Problema**: una evaluación y una clase en vivo permiten operaciones distintas según su fase;
  repartir `if estado == ...` por los casos de uso sería frágil.
- **Evaluaciones**: contexto `Assessment` (`app/modules/assessments/domain/models.py`) delega
  `add_question`, `publish`, `submit_attempt` y `close` en `AssessmentState`
  (`DraftState` → `PublishedState` → `ClosedState`, en `app/modules/assessments/domain/states.py`).
  Publicar exige ≥ 1 pregunta. La calificación es automática (`_grade_and_record`) y respeta `max_attempts`.
- **Clases en vivo**: contexto `LiveSession` (`app/modules/live_sessions/domain/models.py`) delega `start`,
  `end` y `record` en `LiveSessionState` (`ScheduledState` → `LiveState` → `EndedState` → `RecordedState`,
  en `app/modules/live_sessions/domain/states.py`). `LiveSessionService.end` ejecuta `end` y `record`
  seguidos, así que por API el estado pasa de `live` a `recorded` (el estado `ended` es transitorio).
- **Error común**: `InvalidStateTransition` (`app/shared/domain/state.py`) → HTTP 409. Alias en español:
  `BorradorState`, `PublicadaState`, `CerradaState`, `ProgramadaState`, `EnVivoState`, `FinalizadaState`, `GrabadaState`.
- **Endpoints**: `POST /assessments`, `POST /assessments/{assessment_id}/questions`, `/publish`, `/close`,
  `/attempts`, `GET /assessments/{assessment_id}`, `GET /courses/{course_id}/assessments`;
  `POST /live-sessions`, `POST /live-sessions/{session_id}/start`, `/end`, `GET /live-sessions/{session_id}`,
  `GET /courses/{course_id}/live-sessions`.
- **Pruebas**: `test_state.py` (transiciones válidas e inválidas, calificación, nuevo estado con una
  clase, eventos publicados, 409 por API, autorización, certificado una sola vez, ciclo de clase en vivo).
- **Swagger**: como instructor, `POST /assessments` y luego `/publish` sin preguntas → 409; agregar
  pregunta, publicar, cerrar; `/close` otra vez → 409. Para clases: `/start` y `/end` → `recorded`
  con `recording_url`; `/start` de nuevo → 409.
- **Diagramas**: [`uml/state.md`](uml/state.md).

### Visitor

- **Problema**: calcular duración, progreso, resumen y temario sobre el árbol Composite sin `isinstance`
  en el cliente y sin tocar las clases del árbol por cada operación nueva.
- **Clases** (`app/modules/courses/domain/visitor.py`): `ContentVisitor` (ABC: `visit_module`, `visit_lesson`;
  `visit_video_lesson`/`visit_quiz_lesson` delegan en `visit_lesson`; ganchos `visit_course`,
  `leave_course`, `leave_module`), `DurationVisitor`, `ProgressVisitor(completed_lesson_ids)`,
  `ContentSummaryVisitor`, `ExportSyllabusVisitor` (markdown) y `LessonIndexVisitor`.
  `accept()` está en `LessonModule`, `CourseContent`, `VideoLesson`, `InteractiveQuizLesson` y
  `ProtectedContentProxy` (valida acceso y luego delega).
- **Progreso**: `ProgressRepository` (`app/modules/progress/domain/ports.py`), `CompleteLessonUseCase` y
  `GetProgressUseCase` (`app/modules/progress/application/use_cases.py`). Las recomendaciones usan
  `ProgressVisitor` a través de `VisitorProgressReader` (composition root).
- **Endpoints**: `GET /courses/{course_id}/content/summary`, `POST /courses/{course_id}/lessons/{lesson_id}/complete`,
  `GET /courses/{course_id}/progress/me`.
- **Pruebas**: `test_visitor.py` (duración, progreso 0 %/parcial/100 %, resumen por tipo, doble despacho,
  Proxy que bloquea o delega, endpoints 401/403/404/200).
- **Swagger**: como estudiante inscrito, `GET /courses/{id}/content/summary` (`total_minutes`,
  `lessons_by_type`, `syllabus_markdown`); completar una lección y ver `GET /courses/{id}/progress/me`.
- **Diagramas**: [`uml/visitor.md`](uml/visitor.md).

---

## Fe de erratas respecto a la entrega anterior

La entrega anterior es el Word
`Semana 11 Parcial 2/Plataforma_de_Cursos_en_Línea__LMS_Avanzado_ (mejorado).docx`. El Word **no se
modifica**; esta sección lo corrige. Los textos citados se extrajeron de `word/document.xml`.

### D1: Proxy y Facade

| El Word dice | El código real |
|---|---|
| "`PremiumContentProxy`: actúa como intermediario y verifica si el acceso al contenido está permitido" | La clase es `ProtectedContentProxy` (`app/modules/courses/domain/content_proxy.py`). Recibe `real_factory`, `course`, `student_id`, `policy` y `requires_access`. |
| "`CourseContentResource`: representa el recurso real" y "`ContentResource`: define la interfaz" | No existen. El sujeto real es el árbol Composite del curso (`CourseContent`); la interfaz común es `ContentComponent`. La regla de acceso es `EnrolledStudentPolicy` (Protocol `AccessPolicy`). |
| "Se agregó el endpoint `GET /courses/demo-content-access`" con `?premium=…&has_access=…` | No existe. El endpoint real es `GET /courses/{course_id}/content` (token obligatorio). El acceso sale del usuario autenticado y de su inscripción, no de parámetros de la URL. También aplica en `GET /courses/{course_id}/content/summary`. |
| "el proxy lance `PermissionError`" | Lanza `ContentAccessDenied` (subclase de `PermissionError`), que la API traduce a 403. |
| Prueba de la fachada con `CourseFacade()` sin dependencias (señalada en la auditoría; en el Word el código de consola no es texto extraíble) | La firma real es `CourseFacade(repository, payment_checker=None, event_bus=None)`; el repositorio es obligatorio. Ejemplo válido: `CourseFacade(InMemoryCourseRepository())`. Ver `test_new_patterns.py::test_facade_cuatro_operaciones`. |
| "`enroll_student(course_id, student_name)`" | `enroll_student(course_id, user_id, student_name=None)`. La identidad es el `user_id` del token; `student_name` solo se usa en el mensaje. |

### D2: Abstract Factory y Factory Method

| El Word dice | El código real |
|---|---|
| Abstract Factory = `UserUIFactory` con `StudentUIFactory`/`InstructorUIFactory` que crean `NotificationService` y `DashboardService` | No existen. El Abstract Factory real es `UserCreationService` + `UserFactory` (ABC) + `StudentFactory`, `InstructorFactory`, `AdminFactory`. |
| "La implementación se encuentra en: `app/shared/factories/abstract_factories.py`" | Ese archivo no existe (tampoco la carpeta `app/shared/factories/`). La implementación está en `app/modules/auth/domain/factories.py`. |
| Factory Method = `UserFactory.create_user(...)` que analiza el rol y crea `StudentUser`/`InstructorUser`/`AdminUser` (`UserRole`) | En el código, `UserFactory` es la fábrica abstracta. Su `create_user(first_name, last_name, email, password_hash, **extra_fields)` no recibe rol. Quien elige por rol es `UserCreationService.register_user(role, ...)`. Los productos son `Student`, `Instructor` y `Administrator` (`app/modules/auth/domain/models.py`). El Factory Method real del proyecto es `CourseFactory.create_course` (cursos). |
| Se usa "desde `app/main.py`" y en "`POST /users/`" | `main.py` no crea usuarios. El registro es `POST /auth/register` → `RegisterUserUseCase` → `UserCreationService`. `/users/` solo tiene `GET` (admin). |

### Observer

| El Word dice | El código real |
|---|---|
| "Observer — `Subject`, se dispara en `POST /courses/{id}/enroll` y notifica a dos observadores (correo y auditoría)" | Hay un único bus (`event_bus`) con **6 observadores**: `AuditLogObserver`, `EmailNotificationObserver`, `InAppNotificationObserver`, `AutoEnrollOnPaymentObserver`, `CertificateIssuerObserver` y `RecommendationProfileObserver`. Se dispara con 8 tipos de evento, no solo con la inscripción (ver tabla de Observer arriba). |

### Omisiones

- El Word no menciona **State** ni **Visitor**. Ambos están implementados (ver secciones anteriores).
- El Word habla de "seis patrones implementados" en su tabla de lectura; hoy hay 15 (más Strategy en recomendaciones).

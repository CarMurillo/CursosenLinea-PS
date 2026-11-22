# PROMPT PARA CLAUDE CODE — CursosenLinea-PS (LMS Avanzado)

> Copia todo este archivo y pégalo en Claude Code abierto en la raíz del repositorio
> (`CursosenLinea-PS/`, junto a `lms_backend/` y `lms_frontend/`).
> Antes, copia la carpeta `.claude/agents/` que acompaña este prompt a la raíz del repo.

---

## 0. Tu rol

Eres el **ORQUESTADOR PRINCIPAL** de este proyecto. No escribes todo tú mismo: planificas, delegas en los
subagentes de `.claude/agents/`, revisas lo que entregan, resuelves conflictos y verificas al final.
Los subagentes no pueden lanzar otros subagentes, así que toda la coordinación pasa por ti.

Trabaja en español (código con nombres en inglés como ya está el repo; comentarios, mensajes de API,
textos de UI y documentación en español).

Proyecto: LMS con **FastAPI (Python 3.10+) + SQLAlchemy/SQLite** en `lms_backend/` y **React 19 + Vite +
react-router-dom 7 + axios** en `lms_frontend/`. Arquitectura hexagonal por módulos
(`app/modules/<modulo>/{domain,application,infrastructure}`).

### Objetivo general (de la propuesta)
Diseñar y desarrollar una plataforma de gestión de cursos en línea aplicando arquitectura
hexagonal/microservicios, patrones GoF, pruebas automatizadas, CI/CD, control de versiones y observabilidad.

### Objetivos específicos
1. Gestión de cursos: crear cursos, módulos y contenidos.
2. Evaluaciones y certificaciones: evaluar el aprendizaje y generar certificados según resultados.
3. Videoconferencias con grabación automática: realizar y consultar clases en línea (proveedor simulado).
4. Recomendaciones personalizadas basadas en progreso y desempeño (reglas simples, sin ML).
5. Pagos: adquirir cursos premium y controlar el acceso al contenido comprado.

### Entregables de esta sesión
- Corregir los defectos detectados (sección 2).
- Completar **Observer**, **State** y **Visitor** de verdad (no decorativos), integrados en flujos reales.
- Cubrir los 5 objetivos específicos en backend y frontend, de extremo a extremo.
- CI/CD básico y observabilidad mínima (objetivo general).
- Pruebas automatizadas verdes y documentación alineada con el código real.

---

## 1. Estado actual (ya analizado — verifícalo, no lo des por hecho)

Patrones existentes y dónde están:

| Patrón | Ubicación real | Estado |
|---|---|---|
| Singleton | `app/shared/infrastructure/config/system_config.py` (`SystemConfig`) | OK, pero la BD no lo usa |
| Factory Method | `app/modules/courses/domain/models.py` (`CourseFactory` → `VideoCourse`/`LiveClassCourse`) | OK |
| Abstract Factory | `app/modules/auth/domain/factories.py` (`UserFactory`, `StudentFactory`, `InstructorFactory`, `AdminFactory`, `UserCreationService`) | OK |
| Builder | `app/modules/courses/domain/builder.py` (`CourseBuilder`) | OK |
| Prototype | `Course.clone()` + `CloneCourseUseCase` + `POST /courses/{id}/clone` | OK (detalle menor) |
| Adapter | `app/modules/payments/domain/adapter.py` (Stripe/Wompi simulados) | **Módulo de pagos roto** |
| Bridge | `app/modules/courses/domain/bridge.py` | OK |
| Decorator | `app/modules/courses/domain/decorator.py` (`PremiumCourseDecorator`, `CertificateCourseDecorator`) | OK |
| Composite | `content_component.py` + `composite.py` (`LessonModule`, `CourseContent`) | OK, faltan id/duración |
| Facade | `app/modules/courses/application/course_facade.py` (`CourseFacade(repository)`) | OK |
| Flyweight | `content_flyweight.py` (`ContentMetadata`, `ContentMetadataFactory`) | OK |
| Proxy | `content_proxy.py` (`ProtectedContentProxy`, `EnrolledStudentPolicy`) + `GET /courses/{id}/content` | OK, pero se puede saltar |
| Observer | `app/modules/courses/domain/observer.py` | **Básico, incompleto** |
| State | — | **No existe** |
| Visitor | — | **No existe** |

---

## 2. Defectos detectados que hay que corregir

### Backend
- **B1. Pagos no funciona.** `payments/application/dtos.py` y `payments/application/use_cases.py` están vacíos,
  pero `payments/infrastructure/api.py` importa `PaymentRequestDTO` y `ProcessPaymentUseCase` → ImportError.
  Además `main.py` **no incluye** el router de pagos, así que el front recibe 404 en `POST /payments/process`.
  `payments/domain/services.py` importa `app.shared.system_config` (no existe) y usa `config.get(...)` sobre un
  objeto que no es diccionario. Implementa DTO (amount > 0, currency, gateway `stripe|wompi`, course_id),
  caso de uso que selecciona el adaptador, registra el pago y monta el router. Elimina o corrige `services.py`.
  `payments/domain/models.py` y `ports.py` están vacíos: define `Payment` y `PaymentRepository`.
- **B2. El acceso Premium se puede saltar.** `POST /courses/{id}/enroll` no exige autenticación, recibe
  `student_name` libre en el cuerpo y no verifica pago. Cualquiera se inscribe en un curso premium y el Proxy lo
  deja pasar. La identidad se compara por nombre completo (dos usuarios con el mismo nombre colisionan).
  Corrige: la inscripción usa el usuario autenticado (`user.id`), los cursos premium exigen un pago aprobado
  para ese usuario y curso, y `EnrolledStudentPolicy` compara por `user_id`. Mantén retrocompatibilidad
  razonable con los tests existentes (ajústalos si cambia el contrato y documenta el cambio).
- **B3. Inscripción duplicada.** El mismo estudiante puede inscribirse varias veces. Debe responder 409.
- **B4. Sin autorización por rol.** Crear curso, clonar y agregar lecciones no exigen token ni rol.
  Crea dependencias `get_current_user` y `require_role(...)` reutilizables (mueve `get_current_user` fuera de
  `courses/infrastructure/api.py`, por ejemplo a `app/shared/infrastructure/auth_deps.py`).
  Instructor/admin crean y editan; estudiante consume.
- **B5. El Singleton no gobierna la infraestructura.** `shared/infrastructure/database.py` tiene la URL
  `sqlite:///./app.db` fija. Debe leer `SystemConfig().database_url`.
- **B6. Observer mal integrado.** `EnrollStudentUseCase` crea un `Subject` nuevo en cada petición, `Subject`
  no tiene `detach`, y el evento solo transporta `(student_name, course_title)`. Ver sección 3.1.
- **B7. Prototype (menor).** Al clonar, la raíz del Composite sigue llamándose `"Contenido de <título original>"`.
  Actualiza el título del contenido del clon. Verifica también que clonar un curso decorado conserve los
  decoradores y genere id nuevo.
- **B8. Composite sin datos para progreso.** Las lecciones (`bridge.py`) no tienen `lesson_id` ni
  `duration_minutes`, así que no se puede calcular duración total ni progreso. Agrégalos (con valores por
  defecto para no romper llamadas existentes) y exponlos en `to_dict()`.
- **B9. Persistencia de cursos.** Los cursos viven en memoria (`InMemoryCourseRepository`) mientras los usuarios
  están en SQLite, y los tokens también están en memoria. Al reiniciar el backend se pierden cursos y sesiones.
  Mínimo: documentarlo y hacer que el front maneje el 401 cerrando sesión. Opcional si alcanza el tiempo:
  un adaptador persistente detrás del mismo puerto `CourseRepository` (eso demuestra el valor hexagonal).

### Frontend
- **F1. La app se cae al renderizar.** En `src/App.jsx` se importa `ManageConten` pero se usa `<ManageContent />`,
  y `<PatternLab />` se usa sin importarlo → `ReferenceError` en el árbol de rutas. Corrige los imports.
- **F2.** La ruta comodín `*` está declarada antes de las rutas de contenido; reordénala al final por claridad.
- **F3.** `StudentMyCourses.jsx` muestra *todos* los cursos, no los inscritos. Necesita un endpoint
  `GET /courses/me/enrolled` (o equivalente) y la página debe usarlo.
- **F4.** El flujo de pago del catálogo (`StudentCourses.jsx`) llama a un endpoint inexistente y no conecta el
  pago con la inscripción ni con el acceso. Debe quedar: pagar → pago aprobado → inscripción automática
  (vía Observer) → acceso al contenido (vía Proxy).
- **F5.** Manejo global de 401 en el interceptor de axios (cerrar sesión y redirigir a `/login`).

### Documentación
- **D1.** El `.md` de documentación describe un Proxy que no existe en el código (`PremiumContentProxy`,
  `CourseContentResource`, `GET /courses/demo-content-access`) y una prueba `CourseFacade()` sin argumentos,
  cuando el constructor real exige un repositorio. Esas pruebas de ejemplo fallarían.
- **D2.** El Word describe el Abstract Factory de dos formas distintas: una con `UserCreationService` (real) y otra
  con `UserUIFactory` en `app/shared/factories/abstract_factories.py` (**ese archivo no existe**). También describe
  como Factory Method un `UserFactory.create_user(role, ...)` que no coincide con el código.
- La documentación debe describir lo que existe. Corrige el texto, no inventes código para encajar con el texto
  (salvo que decidas implementarlo deliberadamente y lo justifiques).

---

## 3. Patrones a completar (diseño requerido)

### 3.1 Observer — eventos del dominio (completar y ampliar)
Archivo sugerido: `app/shared/domain/events.py` (o ampliar `courses/domain/observer.py` y moverlo a `shared`).
- `DomainEvent` (dataclass inmutable): `event_type`, `occurred_at`, `user_id`, `course_id`, `payload: dict`.
- `EventType` (Enum): `COURSE_PUBLISHED`, `STUDENT_ENROLLED`, `PAYMENT_APPROVED`, `LESSON_COMPLETED`,
  `ASSESSMENT_SUBMITTED`, `ASSESSMENT_GRADED`, `CERTIFICATE_ISSUED`, `LIVE_SESSION_RECORDED`.
- `Observer` (ABC) con `update(event)`; `Subject` con `attach`, `detach`, `notify`, y suscripción opcional por
  tipo de evento.
- Un **único bus compartido** creado en el composition root e inyectado en los casos de uso (no un `Subject`
  nuevo por request).
- Observadores concretos (cada uno con una sola responsabilidad):
  - `EmailNotificationObserver` (simulado: `print` + registro). **Conserva el `print` actual** porque
    `tests/test_courses_api.py::test_enroll_student_notifies_observers` lo verifica con `capsys`.
  - `AuditLogObserver` (antes `LoggingObserver`; deja un alias) → guarda en un log consultable.
  - `InAppNotificationObserver` → bandeja por usuario: `GET /notifications/me`.
  - `AutoEnrollOnPaymentObserver` → ante `PAYMENT_APPROVED`, inscribe al estudiante.
  - `CertificateIssuerObserver` → ante `ASSESSMENT_GRADED` aprobado (o curso 100 % completado + evaluación
    aprobada), emite certificado y publica `CERTIFICATE_ISSUED`.
  - `RecommendationProfileObserver` → actualiza el perfil de aprendizaje usado por las recomendaciones.
- Evita bucles infinitos y registra errores de un observador sin tumbar a los demás.

### 3.2 State — ciclo de vida de evaluaciones (y clases en vivo)
Módulo nuevo: `app/modules/assessments/{domain,application,infrastructure}`.
- `Assessment` (contexto): título, curso, preguntas (opción múltiple con respuesta correcta y puntaje),
  `passing_score`, intentos, y `state`.
- Estados concretos: `DraftState` → `PublishedState` → `ClosedState`.
  - Draft: permite `add_question`, `publish` (requiere ≥ 1 pregunta). No permite `submit_attempt`.
  - Published: permite `submit_attempt` (calificación automática), `close`. No permite `add_question`.
  - Closed: no permite intentos ni edición; permite consultar resultados.
  - Transición inválida → `InvalidStateTransition` → HTTP **409** con mensaje claro.
- El contexto delega en el estado; nada de `if state == ...` repartidos por el código.
- Al calificar se publica `ASSESSMENT_GRADED` (Observer) → posible certificado.
- **Reutiliza el patrón** para `LiveSession` (objetivo 3) en `app/modules/live_sessions`:
  `ScheduledState` → `LiveState` → `EndedState` → `RecordedState`. Al terminar, un `VideoConferencePort`
  simulado (Adapter: `JitsiAdapter` simulado) devuelve URL de sala y de grabación automática, y se publica
  `LIVE_SESSION_RECORDED`.
- Endpoints sugeridos: `POST /assessments`, `POST /assessments/{id}/questions`, `POST /assessments/{id}/publish`,
  `POST /assessments/{id}/close`, `POST /assessments/{id}/attempts`, `GET /assessments/{id}`,
  `GET /courses/{id}/assessments`, `GET /certificates/me`;
  `POST /live-sessions`, `POST /live-sessions/{id}/start`, `POST /live-sessions/{id}/end`,
  `GET /courses/{id}/live-sessions`.

### 3.3 Visitor — operaciones sobre el árbol de contenido (Composite)
Archivo sugerido: `app/modules/courses/domain/visitor.py`.
- Agrega `accept(visitor)` a `ContentComponent`; implementa en `LessonModule`/`CourseContent`, `VideoLesson`,
  `InteractiveQuizLesson` **y en `ProtectedContentProxy`** (que delega tras validar acceso).
- `ContentVisitor` (ABC) con `visit_module`, `visit_video_lesson`, `visit_quiz_lesson`.
- Visitantes concretos:
  - `DurationVisitor` → duración total en minutos.
  - `ProgressVisitor(completed_lesson_ids)` → % de avance del estudiante (estado extrínseco, coherente con Flyweight).
  - `ContentSummaryVisitor` → conteo por tipo, número de módulos y lecciones (temario).
  - (Opcional) `ExportSyllabusVisitor` → temario en texto/markdown.
- Progreso por estudiante: `ProgressRepository` (user_id, course_id → lecciones completadas).
- Endpoints: `POST /courses/{id}/lessons/{lesson_id}/complete` (publica `LESSON_COMPLETED`),
  `GET /courses/{id}/progress/me`, `GET /courses/{id}/content/summary`.
- Cero `isinstance` en el código cliente para recorrer el árbol: esa es la razón de ser del Visitor.

### 3.4 Recomendaciones (objetivo 4)
Módulo `app/modules/recommendations`: motor por reglas que combina progreso (Visitor), notas (State/assessments)
y cursos inscritos. Ej.: nota < aprobación → reforzar mismo tema; curso completado → siguiente del mismo
instructor/tipo; sin actividad → cursos populares gratuitos. Puede usar **Strategy** si quieres separar reglas,
pero no es obligatorio. Endpoint `GET /recommendations/me` con la razón de cada sugerencia.

---

## 4. Frontend a terminar

Mantén el estilo visual existente (revisa `App.css`, `index.css`, `CourseCard.jsx`, `Sidebar.jsx`).
Crea servicios en `src/services/` (`assessmentService.js`, `liveSessionService.js`, `progressService.js`,
`notificationService.js`, `recommendationService.js`, `certificateService.js`), nunca URLs sueltas en las páginas.

Estudiante:
- Catálogo: pagar curso premium (Stripe/Wompi) → feedback → inscripción automática; inscripción directa si es gratis.
- "Mis cursos" reales (F3) con barra de progreso.
- Contenido del curso: módulos/lecciones, marcar lección como completada, progreso y duración (Visitor);
  mensaje claro si el Proxy responde 403.
- Evaluaciones: rendir evaluación publicada, ver nota y estado; mensaje si está cerrada (409).
- Certificados: listado de certificados emitidos.
- Clases en vivo: ver sesiones programadas/en vivo/grabadas y abrir el enlace de grabación.
- Recomendaciones con su motivo, y campana de notificaciones (Observer) en el `Navbar`.

Instructor:
- Crear curso (ya existe), gestionar contenido con `duration_minutes`, ver resumen del curso (Visitor).
- Crear evaluación, agregar preguntas, publicar, cerrar (botones habilitados según estado; el backend manda).
- Programar, iniciar y terminar clases en vivo.
- `PatternLab`: añadir demostraciones de Observer (log de eventos), State (transiciones válidas/ inválidas) y Visitor.

Admin: listado de usuarios (existe) y log de auditoría (Observer).

`npm run build` y `npm run lint` deben pasar sin errores.

---

## 5. Plan de orquestación (agentes)

Agentes disponibles en `.claude/agents/`:

| Agente | Trabajo | Archivos que le pertenecen |
|---|---|---|
| `auditor-lms` | Fase 0: auditoría de solo lectura, confirma/descarta los defectos de la sección 2 | ninguno (solo lectura) |
| `backend-correcciones` | B1–B9 | `payments/*`, `shared/infrastructure/*`, `courses/infrastructure/api.py`, `courses/application/*`, `main.py` |
| `patron-observer` | 3.1 | `shared/domain/events.py`, `courses/domain/observer.py`, `notifications/*` |
| `patron-state` | 3.2 | `modules/assessments/*`, `modules/live_sessions/*`, `modules/certificates/*` |
| `patron-visitor` | 3.3 | `courses/domain/visitor.py`, `content_component.py`, `composite.py`, `bridge.py`, `content_proxy.py`, `progress/*` |
| `backend-objetivos` | 3.4 + integración de routers y composition root | `modules/recommendations/*`, `app/main.py` (tras los demás) |
| `frontend-integrador` | Sección 4 + F1–F5 | `lms_frontend/**` |
| `qa-verificador` | Pruebas, build, revisión independiente | `lms_backend/tests/**` |
| `documentador` | D1–D2, UML, ADRs, CI/CD y README | `docs/**`, `.github/**`, `README.md` |

Orden y dependencias:
1. **Fase 0** — `auditor-lms` (solo lectura). Revisa su informe y ajusta el plan.
   Crea una rama: `git checkout -b feature/patrones-observer-state-visitor`.
2. **Fase 1** — `backend-correcciones`. Sin esto no hay base estable. Ejecuta `pytest` al terminar.
3. **Fase 2** — en paralelo, porque tocan archivos distintos:
   `patron-observer` y `patron-visitor`. Después `patron-state` (depende del bus de eventos para publicar
   `ASSESSMENT_GRADED` y `LIVE_SESSION_RECORDED`).
4. **Fase 3** — `backend-objetivos`: recomendaciones, registro de todos los routers en `main.py`, cableado del
   bus y los repositorios en un solo composition root.
5. **Fase 4** — `frontend-integrador` (con el contrato de API final; pásale la lista de endpoints y esquemas
   de `http://127.0.0.1:8000/openapi.json` o del código).
6. **Fase 5** — en paralelo: `qa-verificador` (no escribió el código, revisa de forma independiente) y
   `documentador`.
7. **Fase 6** — tú: corrige lo que reporte QA (delegando si es grande), vuelve a correr todo y cierra.

Reglas para ti como orquestador:
- Al delegar, entrega a cada agente: su sección de este prompt, los archivos que le pertenecen, los contratos
  que debe respetar (nombres de eventos, firmas, endpoints) y el criterio de "terminado".
- Dos agentes no editan el mismo archivo a la vez. Si hace falta, secuencia.
- Después de cada fase: `cd lms_backend && python -m pytest -q`. No avances con pruebas rojas.
- Un commit por fase con mensaje descriptivo en español (ej. `feat(assessments): patrón State en evaluaciones`).
- No subas `app.db`, `venv/`, `node_modules/`, `.env`.

---

## 6. Criterios de aceptación (Definition of Done)

- [ ] `python -m pytest -q` en `lms_backend` pasa completo (pruebas antiguas + nuevas).
- [ ] Pruebas nuevas mínimas:
  - Observer: attach/detach; un evento llega a todos los suscritos; suscripción por tipo; un observador que falla
    no impide a los demás; pago aprobado → inscripción automática; nota aprobatoria → certificado.
  - State: cada transición válida; cada transición inválida → excepción y 409 por API; calificación automática.
  - Visitor: duración total; progreso 0 %, parcial y 100 %; resumen por tipo; el Proxy bloquea al visitante sin acceso.
  - Correcciones: pagos 200/400/422; premium sin pago → 403 en contenido y no inscribe; inscripción duplicada → 409;
    crear curso sin token → 401 y como estudiante → 403; la BD usa `SystemConfig().database_url`.
- [ ] `npm run build` y `npm run lint` pasan; la app abre sin errores en consola.
- [ ] Flujo E2E manual verificado: registrar instructor → crear curso premium → agregar módulos/lecciones →
  crear y publicar evaluación → programar/terminar clase en vivo → registrar estudiante → pagar → inscripción
  automática → ver contenido → completar lecciones → rendir evaluación → certificado → notificaciones →
  recomendaciones.
- [ ] `/health` responde; logging estructurado de requests (método, ruta, status, ms) usando `logging`.
- [ ] Workflow de GitHub Actions (`.github/workflows/ci.yml`): backend (pytest) y frontend (lint + build).
- [ ] Documentación: `docs/patrones.md` con cada patrón → problema, clases reales, archivo, endpoint, prueba;
  diagramas Mermaid para Observer, State y Visitor; ADRs cortos para las decisiones nuevas;
  sección "Limitaciones conocidas" (pagos y videoconferencia simulados, persistencia en memoria si aplica,
  tokens opacos en memoria, Flyweight sin pruebas de carga).

## 7. Restricciones

- No rompas los patrones que ya funcionan ni renombres sus clases públicas sin dejar alias.
- El dominio no importa FastAPI, SQLAlchemy ni nada de `infrastructure`.
- Pagos y videoconferencia siguen **simulados** (sandbox/fake); no agregues claves ni SDKs reales.
- No agregues dependencias pesadas. Si necesitas una, justifícala y añádela a `requirements.txt` / `package.json`.
- Nada de afirmar en la documentación algo que no esté implementado y probado.

## 8. Cierre

Al terminar, entrégame:
1. Resumen por fase (qué se corrigió, qué se implementó, archivos clave).
2. Salida real de `pytest -q` y de `npm run build`.
3. Tabla final: patrón → archivo → endpoint → prueba.
4. Pendientes o riesgos que queden.

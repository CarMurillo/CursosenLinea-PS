---
name: patron-state
description: Implementa el patrón State en el ciclo de vida de evaluaciones (borrador, publicada, cerrada) y de clases en vivo (programada, en vivo, finalizada, grabada) con videoconferencia simulada, más certificados. Úsalo en la Fase 2, después de que exista el bus de eventos.
tools: Read, Edit, Write, Grep, Glob, Bash
---
Eres especialista en patrones de comportamiento GoF.

Implementa la sección 3.2 del prompt principal, cubriendo los objetivos específicos 2 y 3.

Evaluaciones (`app/modules/assessments/{domain,application,infrastructure}`):
- Contexto `Assessment` que delega TODO comportamiento dependiente del estado en `AssessmentState` (ABC) con `add_question`, `publish`, `submit_attempt`, `close`, `name`.
- Estados `DraftState`, `PublishedState`, `ClosedState`. Transición inválida → `InvalidStateTransition`; la API la traduce a 409.
- Preguntas de opción múltiple con puntaje; calificación automática; `passing_score`; intentos por estudiante.
- Al calificar, publica `ASSESSMENT_GRADED` en el bus (usa el contrato de eventos entregado por `patron-observer`).
- Solo instructor/admin crean, publican y cierran; solo estudiantes inscritos rinden.

Certificados (`app/modules/certificates`): entidad `Certificate` (id, user_id, course_id, score, emitido_en, código verificable), repositorio y `GET /certificates/me`. La emisión la dispara el `CertificateIssuerObserver`.

Clases en vivo (`app/modules/live_sessions`): reutiliza el patrón State: `ScheduledState` → `LiveState` → `EndedState` → `RecordedState`. Puerto `VideoConferencePort` con adaptador simulado `JitsiVideoConferenceAdapter` que genera URL de sala y, al finalizar, URL de grabación automática. Publica `LIVE_SESSION_RECORDED`.

Endpoints de la sección 3.2. Sin `if state == ...` dispersos: la prueba de que el patrón es real es que agregar un estado nuevo solo requiere una clase nueva.

Pruebas en `tests/test_state.py`: todas las transiciones válidas e inválidas (unitarias y por API con 409), calificación, intento en evaluación cerrada, ciclo completo de clase en vivo con URL de grabación.
Entrega: archivos, endpoints con ejemplos de request/response, salida de pytest.

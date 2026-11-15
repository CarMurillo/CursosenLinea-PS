# ADR 0002: Patrón State para evaluaciones y clases en vivo

- Estado: aceptado
- Código: `app/modules/assessments/domain/models.py`, `app/modules/assessments/domain/states.py`,
  `app/modules/live_sessions/domain/models.py`, `app/modules/live_sessions/domain/states.py`,
  `app/shared/domain/state.py`

## Contexto

Una evaluación solo admite preguntas en borrador, intentos cuando está publicada y nada cuando está
cerrada. Una clase en vivo pasa por programada, en vivo, finalizada y grabada. Con condicionales
`if estado == ...` repartidos en casos de uso y endpoints, cada regla nueva tocaría varios archivos.

## Decisión

- `Assessment` y `LiveSession` son contextos que delegan toda operación dependiente del estado en un
  objeto estado (`AssessmentState`: `DraftState`, `PublishedState`, `ClosedState`;
  `LiveSessionState`: `ScheduledState`, `LiveState`, `EndedState`, `RecordedState`).
- Los estados cambian el estado del contexto con `_transition_to`.
- Toda operación no permitida lanza `InvalidStateTransition`; la capa HTTP la traduce a 409.
- `POST /live-sessions/{session_id}/end` ejecuta `end` y `record` seguidos (grabación automática
  simulada), así que `ended` es transitorio vía API.

## Consecuencias

- Positivas: sin condicionales de estado en los servicios; añadir un estado es añadir una clase
  (`test_state.py::test_nuevo_estado_solo_requiere_una_clase`); mensajes 409 consistentes.
- Negativas: más clases pequeñas. El estado vive en memoria como objeto; persistirlo exigirá mapear
  `state_name` a su clase al leer.

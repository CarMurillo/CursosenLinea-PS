# ADR 0001: Bus de eventos síncrono en memoria (Observer)

- Estado: aceptado
- Código: `app/shared/domain/events.py`, `app/shared/domain/observers.py`, `app/shared/infrastructure/container.py`

## Contexto

Antes, `EnrollStudentUseCase` creaba un `Subject` nuevo en cada petición, `Subject` no tenía `detach` y
el evento solo llevaba `(student_name, course_title)`. Los nuevos requisitos necesitan reaccionar a
varios hechos: pago aprobado → inscripción, nota aprobatoria → certificado, grabación → aviso a
inscritos, auditoría y perfil de recomendaciones. Todo corre en un único proceso de uvicorn.

## Decisión

- Un único `Subject` (`event_bus`) creado en el composition root e inyectado en los casos de uso a
  través del puerto `EventPublisher`.
- `DomainEvent` inmutable con `event_type` (`EventType`, 8 valores), `user_id`, `course_id`, `payload`,
  `occurred_at` y `event_id`.
- Suscripción opcional por tipo: `attach(observer, event_types)`.
- Difusión **síncrona**, en el hilo de la petición. Un observador que falla se registra con `logging`
  y no detiene a los demás. Guardas contra bucles: reentrada por (observador, tipo) y profundidad
  máxima 8.

## Consecuencias

- Positivas: sin dependencias nuevas; los casos de uso no conocen a los observadores; el flujo es
  determinista y fácil de probar (`test_observer.py`).
- Negativas: un observador lento alarga la respuesta HTTP. Los eventos se pierden si el proceso cae
  (no hay cola ni persistencia). No escala a varios procesos o réplicas. Si un observador falla, el
  publicador no se entera (por ejemplo, el pago queda aprobado aunque la auto-inscripción falle).
- Evolución posible: otro `EventPublisher` (cola o broker) detrás del mismo puerto.

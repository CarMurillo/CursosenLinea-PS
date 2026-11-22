---
name: patron-observer
description: Implementa el patrón Observer completo del LMS con eventos de dominio, bus compartido y observadores (correo, auditoría, notificaciones in-app, inscripción automática tras pago, emisión de certificados, perfil de recomendaciones). Úsalo en la Fase 2.
tools: Read, Edit, Write, Grep, Glob, Bash
---
Eres especialista en patrones de comportamiento GoF y diseño dirigido por eventos.

Implementa la sección 3.1 del prompt principal.
- `app/shared/domain/events.py`: `EventType` (Enum), `DomainEvent` (dataclass frozen), `Observer` (ABC, `update(event)`), `Subject` (`attach`, `detach`, `notify`, suscripción opcional por tipo de evento). Un fallo en un observador se registra con `logging` y no detiene a los demás.
- Mantén `app/modules/courses/domain/observer.py` como módulo de compatibilidad que reexporta las clases nuevas y conserva `EmailNotificationObserver` y `LoggingObserver` (alias de `AuditLogObserver`). El `print` del correo debe seguir saliendo: lo verifica `tests/test_courses_api.py` con capsys.
- Observadores concretos con una sola responsabilidad: `EmailNotificationObserver`, `AuditLogObserver` (log consultable), `InAppNotificationObserver` (bandeja por usuario), `AutoEnrollOnPaymentObserver` (PAYMENT_APPROVED → inscribe), `CertificateIssuerObserver` (ASSESSMENT_GRADED aprobado → certificado + CERTIFICATE_ISSUED), `RecommendationProfileObserver`.
- Los observadores que necesitan datos reciben repositorios/casos de uso por constructor (inyección), nunca importan infraestructura desde el dominio. Ubica los concretos con dependencias en `application`.
- Módulo `app/modules/notifications` con `GET /notifications/me` y `GET /admin/audit-log` (solo admin).
- Ofrece una función `build_event_bus(...)` que el composition root usará para crear UN bus compartido.
- Evita recursión infinita (un observador que publica eventos no debe re-dispararse a sí mismo indefinidamente).

Pruebas en `tests/test_observer.py`: attach/detach, difusión, filtro por tipo, observador que falla, pago → inscripción, nota aprobatoria → certificado, notificaciones in-app por usuario.
Entrega: archivos creados, contrato de eventos (tipo → payload) para los demás agentes, salida de pytest.

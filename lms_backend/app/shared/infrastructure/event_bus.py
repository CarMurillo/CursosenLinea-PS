"""Bus de eventos PROVISIONAL (Fase 1).

Corrige B6: en lugar de crear un Subject por request, se crea UNA sola
instancia compartida con sus observadores y se inyecta en los casos de uso.
La Fase 2 lo reemplaza por el bus de `app/shared/domain/events.py`
construido en el composition root (`container.py`).
"""

from app.modules.courses.domain.observer import (
    EmailNotificationObserver,
    LoggingObserver,
    Subject,
)


def build_enrollment_notifier() -> Subject:
    subject = Subject()
    subject.attach(EmailNotificationObserver())
    subject.attach(LoggingObserver())
    return subject


# Instancia única compartida por la aplicación.
enrollment_notifier = build_enrollment_notifier()

"""CertificateIssuerObserver: ASSESSMENT_GRADED aprobado -> certificado."""

import logging
from typing import List

from app.modules.certificates.domain.ports import CertificateIssuerPort
from app.shared.domain.events import (
    DomainEvent,
    EventPublisher,
    EventType,
    Observer,
)

logger = logging.getLogger(__name__)


class CertificateIssuerObserver(Observer):
    """Ante ASSESSMENT_GRADED con `payload["passed"] == True` emite el
    certificado (vía puerto inyectado) y publica CERTIFICATE_ISSUED en el bus
    inyectado. Si el certificado ya existía (issuer devuelve None) no publica
    nada, así que reintentos o notas repetidas no generan eventos duplicados.
    """

    def __init__(self, issuer: CertificateIssuerPort, publisher: EventPublisher):
        self._issuer = issuer
        self._publisher = publisher

    @staticmethod
    def subscribed_events() -> List[EventType]:
        return [EventType.ASSESSMENT_GRADED]

    def update(self, event: DomainEvent) -> None:
        if event.event_type != EventType.ASSESSMENT_GRADED:
            return
        if not event.payload.get("passed"):
            return
        if not event.user_id or not event.course_id:
            logger.warning("ASSESSMENT_GRADED sin user_id/course_id: %s", event.event_id)
            return

        certificate = self._issuer.issue(event.user_id, event.course_id, event.payload)
        if certificate is None:
            return

        self._publisher.notify(DomainEvent(
            EventType.CERTIFICATE_ISSUED,
            user_id=event.user_id,
            course_id=event.course_id,
            payload={
                "certificate_id": certificate.get("certificate_id"),
                "assessment_id": event.payload.get("assessment_id"),
                "score": event.payload.get("score"),
                "course_title": event.payload.get("course_title"),
            },
        ))

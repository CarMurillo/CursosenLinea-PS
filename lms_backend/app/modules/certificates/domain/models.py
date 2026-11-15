"""Entidad `Certificate` con código de verificación."""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def new_verification_code() -> str:
    """Código legible y no adivinable, p. ej. 'LMS-3F9A-1C77-B20E'."""
    raw = secrets.token_hex(6).upper()
    return f"LMS-{raw[0:4]}-{raw[4:8]}-{raw[8:12]}"


@dataclass
class Certificate:
    user_id: str
    course_id: str
    score: Optional[float] = None
    course_title: Optional[str] = None
    assessment_id: Optional[str] = None
    certificate_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    verification_code: str = field(default_factory=new_verification_code)
    issued_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "certificate_id": self.certificate_id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "course_title": self.course_title,
            "assessment_id": self.assessment_id,
            "score": self.score,
            "verification_code": self.verification_code,
            "issued_at": self.issued_at.isoformat(),
        }

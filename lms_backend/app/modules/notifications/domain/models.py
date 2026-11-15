"""Notificaciones in-app (bandeja por usuario)."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Notification:
    user_id: str
    title: str
    message: str
    event_type: str
    course_id: Optional[str] = None
    read: bool = False
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "event_type": self.event_type,
            "course_id": self.course_id,
            "read": self.read,
            "created_at": self.created_at.isoformat(),
        }

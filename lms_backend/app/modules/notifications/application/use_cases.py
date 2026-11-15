from typing import List, Optional

from app.modules.notifications.domain.models import Notification
from app.modules.notifications.domain.ports import (
    AuditEntry,
    AuditLogRepository,
    NotificationRepository,
)


class ListMyNotificationsUseCase:
    def __init__(self, repository: NotificationRepository):
        self._repository = repository

    def execute(self, user_id: str) -> List[Notification]:
        return self._repository.list_by_user(user_id)


class ListAuditLogUseCase:
    def __init__(self, repository: AuditLogRepository):
        self._repository = repository

    def execute(
        self, event_type: Optional[str] = None, limit: Optional[int] = None
    ) -> List[AuditEntry]:
        return self._repository.list_entries(event_type=event_type, limit=limit)

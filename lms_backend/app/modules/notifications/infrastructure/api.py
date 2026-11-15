"""Endpoints de notificaciones in-app y log de auditoría."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.modules.notifications.application.use_cases import (
    ListAuditLogUseCase,
    ListMyNotificationsUseCase,
)
from app.shared.domain.events import EventType
from app.shared.infrastructure import container
from app.shared.infrastructure.auth_deps import get_current_user, require_role

router = APIRouter(prefix="/notifications", tags=["notifications"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me")
def my_notifications(user=Depends(get_current_user)):
    """Bandeja in-app del usuario autenticado (más recientes primero)."""
    use_case = ListMyNotificationsUseCase(container.notification_repository)
    return [n.to_dict() for n in use_case.execute(user.id)]


@admin_router.get("/audit-log")
def audit_log(
    event_type: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    _admin=Depends(require_role("admin")),
):
    """Log de auditoría de eventos del dominio (solo admin)."""
    if event_type is not None:
        valid = {t.value for t in EventType}
        if event_type not in valid:
            raise HTTPException(
                status_code=422,
                detail=f"event_type inválido. Usa uno de: {sorted(valid)}",
            )
    use_case = ListAuditLogUseCase(container.audit_log_repository)
    return [e.to_dict() for e in use_case.execute(event_type=event_type, limit=limit)]

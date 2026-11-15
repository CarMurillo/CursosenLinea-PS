"""Endpoints de clases en vivo (patrón State + Adapter de videoconferencia).

`router`         -> /live-sessions*
`courses_router` -> GET /courses/{course_id}/live-sessions
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.modules.live_sessions.application.use_cases import LiveSessionService
from app.shared.infrastructure import container
from app.shared.infrastructure.auth_deps import get_current_user, require_role
from app.shared.infrastructure.http_errors import domain_errors_as_http

router = APIRouter(prefix="/live-sessions", tags=["live-sessions"])
courses_router = APIRouter(prefix="/courses", tags=["live-sessions"])

require_staff = require_role("instructor", "admin")


class LiveSessionCreateDTO(BaseModel):
    course_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    scheduled_at: Optional[datetime] = None
    duration_minutes: int = Field(default=60, gt=0, le=600)


def get_live_session_service() -> LiveSessionService:
    return container.make_live_session_service()


@router.post("", status_code=201)
def schedule_live_session(
    dto: LiveSessionCreateDTO,
    user=Depends(require_staff),
    service: LiveSessionService = Depends(get_live_session_service),
):
    with domain_errors_as_http():
        session = service.schedule(
            course_id=dto.course_id,
            title=dto.title,
            scheduled_at=dto.scheduled_at,
            duration_minutes=dto.duration_minutes,
            user_id=user.id,
            role=user.role,
        )
    return session.to_dict()


@router.post("/{session_id}/start")
def start_live_session(
    session_id: str,
    user=Depends(require_staff),
    service: LiveSessionService = Depends(get_live_session_service),
):
    with domain_errors_as_http():
        return service.start(session_id, user_id=user.id, role=user.role).to_dict()


@router.post("/{session_id}/end")
def end_live_session(
    session_id: str,
    user=Depends(require_staff),
    service: LiveSessionService = Depends(get_live_session_service),
):
    with domain_errors_as_http():
        return service.end(session_id, user_id=user.id, role=user.role).to_dict()


@router.get("/{session_id}")
def get_live_session(
    session_id: str,
    user=Depends(get_current_user),
    service: LiveSessionService = Depends(get_live_session_service),
):
    with domain_errors_as_http():
        return service.get_for_user(session_id, user_id=user.id, role=user.role).to_dict()


@courses_router.get("/{course_id}/live-sessions")
def list_course_live_sessions(
    course_id: str,
    user=Depends(get_current_user),
    service: LiveSessionService = Depends(get_live_session_service),
):
    with domain_errors_as_http():
        return [
            s.to_dict()
            for s in service.list_for_course(course_id, user_id=user.id, role=user.role)
        ]

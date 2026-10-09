from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.auth.application.dtos import UserResponseDTO
from app.modules.auth.domain.models import Role
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponseDTO])
def list_users(db: Session = Depends(get_db)):
    repo = SqlAlchemyUserRepository(db)
    return [
        UserResponseDTO(
            user_id=u.id,
            full_name=f"{u.first_name} {u.last_name}",
            email=u.email,
            role=Role(u.role),
            is_active=u.is_active,
            details={},
        )
        for u in repo.get_all()
    ]
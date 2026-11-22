from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.auth.domain.models import User
from app.shared.infrastructure.models import UserModel
from app.users.domain.repositories import UserRepository


class SqlAlchemyUserRepository(UserRepository):
    """Adaptador de salida: implementa el puerto UserRepository con SQLAlchemy.

    Mapea la entidad de dominio `User` al modelo ORM `UserModel` (el dominio
    no conoce SQLAlchemy).
    """

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_model(user: User) -> UserModel:
        return UserModel(
            id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            hashed_password=user.hashed_password,
            role=getattr(user.role, "value", user.role),
            is_active=user.is_active,
        )

    def save(self, user: User) -> UserModel:
        model = self._to_model(user)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_by_id(self, user_id: str) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[UserModel]:
        # Sin distinguir mayúsculas: cubre también filas antiguas guardadas
        # antes de normalizar el correo a minúsculas.
        normalized = (email or "").strip().lower()
        return (
            self.db.query(UserModel)
            .filter(func.lower(UserModel.email) == normalized)
            .first()
        )

    def get_all(self) -> List[UserModel]:
        return self.db.query(UserModel).all()

    def set_active(self, user_id: str, is_active: bool) -> Optional[UserModel]:
        model = self.get_by_id(user_id)
        if model is None:
            return None
        model.is_active = bool(is_active)
        self.db.commit()
        self.db.refresh(model)
        return model

    def delete(self, user_id: str) -> bool:
        model = self.get_by_id(user_id)
        if model is None:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

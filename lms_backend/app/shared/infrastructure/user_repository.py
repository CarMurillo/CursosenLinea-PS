from typing import List, Optional

from sqlalchemy.orm import Session

from app.shared.infrastructure.models import UserModel
from app.users.domain.repositories import UserRepository


class SqlAlchemyUserRepository(UserRepository):
    """Adaptador de salida: implementa el puerto UserRepository con SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    def save(self, user: UserModel) -> UserModel:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: str) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.email == email).first()

    def get_all(self) -> List[UserModel]:
        return self.db.query(UserModel).all()
from abc import ABC, abstractmethod
from typing import List, Optional

from app.shared.infrastructure.models import UserModel


class UserRepository(ABC):
    """Puerto del dominio de usuarios (patrón hexagonal)."""

    @abstractmethod
    def save(self, user: UserModel) -> UserModel:
        pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[UserModel]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[UserModel]:
        pass

    @abstractmethod
    def get_all(self) -> List[UserModel]:
        pass
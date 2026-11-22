from abc import ABC, abstractmethod
from typing import List, Optional, Protocol

from app.modules.auth.domain.models import User


class UserRecord(Protocol):
    """Vista de lectura de un usuario persistido.

    El dominio no conoce el modelo ORM: cualquier objeto con estos atributos
    cumple el contrato (el adaptador SQLAlchemy devuelve `UserModel`).
    """

    id: str
    first_name: str
    last_name: str
    email: str
    hashed_password: str
    role: str
    is_active: bool


class UserRepository(ABC):
    """Puerto del dominio de usuarios (patrón hexagonal).

    Recibe la entidad de dominio `User` y devuelve `UserRecord`; el mapeo a
    la persistencia concreta lo hace el adaptador de infraestructura.
    """

    @abstractmethod
    def save(self, user: User) -> UserRecord:
        pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[UserRecord]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[UserRecord]:
        """Búsqueda sin distinguir mayúsculas/minúsculas."""

    @abstractmethod
    def get_all(self) -> List[UserRecord]:
        pass

    @abstractmethod
    def set_active(self, user_id: str, is_active: bool) -> Optional[UserRecord]:
        """Suspende (False) o reactiva (True). None si el usuario no existe."""

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Elimina el usuario. True si existía."""

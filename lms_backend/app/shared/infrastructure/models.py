from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String

from app.shared.infrastructure.database import Base


class UserModel(Base):
    """Modelo de persistencia (SQLAlchemy) del usuario.

    El id usa el mismo UUID que genera la entidad de dominio `User`
    (app.modules.auth.domain.models), para no duplicar identificadores.
    El rol se guarda como string y se mapea al Enum `Role` del dominio
    de auth al leerlo, para evitar que infraestructura y dominio se
    acoplen a un segundo Enum paralelo.
    """

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.auth.domain.models import Role

# Validación simple y predecible (sin dependencias externas): algo@dominio.tld
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN_LENGTH = 8


class UserRegisterDTO(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=254)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)
    role: Role
    bio: Optional[str] = ""
    specialization: Optional[str] = ""

    @field_validator("first_name", "last_name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre no puede estar vacío.")
        return value

    @field_validator("email")
    @classmethod
    def _valid_email(cls, value: str) -> str:
        # Se normaliza a minúsculas: Dup@x.com y dup@x.com son la misma cuenta.
        value = value.strip().lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Correo electrónico inválido.")
        return value


class UserResponseDTO(BaseModel):
    user_id: str
    full_name: str
    email: str
    role: Role
    is_active: bool
    details: dict


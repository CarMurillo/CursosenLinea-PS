
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.modules.auth.domain.models import Role


class UserRegisterDTO(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    role: Role
    bio: Optional[str] = ""
    specialization: Optional[str] = ""


class UserResponseDTO(BaseModel):
    user_id: str
    full_name: str
    email: str
    role: Role
    is_active: bool
    details: dict


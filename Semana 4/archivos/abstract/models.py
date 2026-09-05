
from enum import Enum
from datetime import datetime
from typing import List
from dataclasses import dataclass, field
import uuid


class Role(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


@dataclass
class User:
    """Entidad Base de Usuario."""
    first_name: str
    last_name: str
    email: str
    hashed_password: str
    role: Role
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class Student(User):
    """Entidad de Estudiante."""
    role: Role = Role.STUDENT
    enrolled_courses: List[str] = field(default_factory=list)
    certificates: List[str] = field(default_factory=list)


@dataclass
class Instructor(User):
    """Entidad de Instructor."""
    role: Role = Role.INSTRUCTOR
    bio: str = ""
    created_courses: List[str] = field(default_factory=list)
    specialization: str = ""


@dataclass
class Administrator(User):
    """Entidad de Administrador."""
    role: Role = Role.ADMIN
    permissions: List[str] = field(default_factory=lambda: ["all"])
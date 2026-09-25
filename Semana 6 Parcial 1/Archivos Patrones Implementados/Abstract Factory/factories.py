
from abc import ABC, abstractmethod
from app.modules.auth.domain.models import User, Student, Instructor, Administrator, Role


class UserFactory(ABC):
    """Fábrica Abstracta para la creación de usuarios."""
    
    @abstractmethod
    def create_user(self, first_name: str, last_name: str, email: str, password_hash: str, **extra_fields) -> User:
        pass


class StudentFactory(UserFactory):
    def create_user(self, first_name: str, last_name: str, email: str, password_hash: str, **extra_fields) -> Student:
        return Student(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=password_hash
        )


class InstructorFactory(UserFactory):
    def create_user(self, first_name: str, last_name: str, email: str, password_hash: str, **extra_fields) -> Instructor:
        bio = extra_fields.get("bio", "")
        specialization = extra_fields.get("specialization", "")
        return Instructor(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=password_hash,
            bio=bio,
            specialization=specialization
        )


class AdminFactory(UserFactory):
    def create_user(self, first_name: str, last_name: str, email: str, password_hash: str, **extra_fields) -> Administrator:
        permissions = extra_fields.get("permissions", ["all"])
        return Administrator(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=password_hash,
            permissions=permissions
        )


class UserCreationService:
    """Servicio Creador Unificado (Abstract Factory)."""
    _factories = {
        Role.STUDENT: StudentFactory(),
        Role.INSTRUCTOR: InstructorFactory(),
        Role.ADMIN: AdminFactory()
    }

    @classmethod
    def register_user(cls, role: Role, first_name: str, last_name: str, email: str, password_hash: str, **extra) -> User:
        factory = cls._factories.get(role)
        if not factory:
            raise ValueError(f"Rol no soportado: {role}")
        return factory.create_user(first_name, last_name, email, password_hash, **extra)

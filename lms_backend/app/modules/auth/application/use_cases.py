"""Casos de uso del módulo de autenticación.

Aquí es donde se conecta el patrón GoF Abstract Factory
(UserCreationService) con la infraestructura real: base de datos y
hashing de contraseñas.
"""

from app.modules.auth.application.dtos import UserRegisterDTO, UserResponseDTO
from app.modules.auth.domain.factories import UserCreationService
from app.modules.auth.domain.models import Role
from app.modules.auth.infrastructure.security import hash_password, issue_token, verify_password
from app.users.domain.repositories import UserRecord, UserRepository


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def normalize_email(email: str) -> str:
    """Correo canónico: sin espacios y en minúsculas."""
    return (email or "").strip().lower()


def _to_response_dto(user_model: UserRecord) -> UserResponseDTO:
    return UserResponseDTO(
        user_id=user_model.id,
        full_name=f"{user_model.first_name} {user_model.last_name}",
        email=user_model.email,
        role=Role(user_model.role),
        is_active=user_model.is_active,
        details={},
    )


class RegisterUserUseCase:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, dto: UserRegisterDTO) -> UserResponseDTO:
        email = normalize_email(dto.email)
        if self.repository.get_by_email(email):
            raise EmailAlreadyRegisteredError(email)

        # --- PATRÓN GOF: ABSTRACT FACTORY ---
        # UserCreationService elige la fábrica concreta (Student/Instructor/
        # Admin) según el rol solicitado y construye la entidad de dominio
        # correspondiente sin que este caso de uso conozca las subclases.
        domain_user = UserCreationService.register_user(
            role=dto.role,
            first_name=dto.first_name,
            last_name=dto.last_name,
            email=email,
            password_hash=hash_password(dto.password),
            bio=dto.bio,
            specialization=dto.specialization,
        )

        # El adaptador de persistencia mapea la entidad de dominio a su modelo.
        saved = self.repository.save(domain_user)
        return _to_response_dto(saved)


class LoginUseCase:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, email: str, password: str) -> tuple[str, UserResponseDTO]:
        user_model = self.repository.get_by_email(normalize_email(email))
        if not user_model or not user_model.is_active or not verify_password(password, user_model.hashed_password):
            raise InvalidCredentialsError()

        token = issue_token(user_model.id)
        return token, _to_response_dto(user_model)
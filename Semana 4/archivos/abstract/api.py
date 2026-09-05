from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.modules.auth.application.dtos import UserRegisterDTO, UserResponseDTO
from app.modules.auth.application.use_cases import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    LoginUseCase,
    RegisterUserUseCase,
)
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponseDTO


@router.post("/register", response_model=UserResponseDTO, status_code=201)
def register(dto: UserRegisterDTO, db: Session = Depends(get_db)):
    """Registra un perfil (estudiante/instructor/admin) vía el Abstract Factory."""
    use_case = RegisterUserUseCase(SqlAlchemyUserRepository(db))
    try:
        return use_case.execute(dto)
    except EmailAlreadyRegisteredError:
        raise HTTPException(status_code=409, detail="El correo ya está registrado.")


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Valida credenciales y entrega un token de sesión."""
    use_case = LoginUseCase(SqlAlchemyUserRepository(db))
    try:
        token, user = use_case.execute(credentials.email, credentials.password)
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    return TokenResponse(access_token=token, user=user)
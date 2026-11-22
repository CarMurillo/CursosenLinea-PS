"""Administración de usuarios (todas las rutas exigen rol admin).

- GET    /users/?role=student|instructor|admin   listado (filtro opcional)
- POST   /users/                                 el admin registra estudiantes o instructores
- GET    /users/{user_id}/detail                 ficha: cursos, estado de avance, certificados, pagos
- PATCH  /users/{user_id}/status                 suspender / reactivar
- DELETE /users/{user_id}                        eliminar (instructor con cursos -> 409)
"""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.modules.auth.application.dtos import UserRegisterDTO
from app.modules.auth.application.use_cases import (
    EmailAlreadyRegisteredError,
    RegisterUserUseCase,
)
from app.shared.infrastructure import container
from app.shared.infrastructure.auth_deps import require_role
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository
from app.users.application.admin_users import (
    MANAGEABLE_ROLES,
    DeleteUserUseCase,
    SetUserStatusUseCase,
    UserDetailService,
    UserHasCoursesError,
    UserNotFoundError,
    UserStatusNotAllowedError,
    user_summary,
)

router = APIRouter(prefix="/users", tags=["users"])
require_admin = require_role("admin")


class UserStatusDTO(BaseModel):
    is_active: bool


def _detail_service(db: Session) -> UserDetailService:
    return UserDetailService(
        users=SqlAlchemyUserRepository(db),
        courses=container.course_repository,
        progress_percent=container.VisitorProgressReader(
            container.course_repository, container.progress_repository
        ).progress_percent,
        certificates=container.certificate_repository,
        payments=container.payment_repository,
    )


@router.get("/")
def list_users(
    role: Optional[Literal["student", "instructor", "admin"]] = Query(default=None),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Listado de usuarios: solo administradores. `role` filtra por rol."""
    users = SqlAlchemyUserRepository(db).get_all()
    if role:
        users = [u for u in users if u.role == role]
    users.sort(key=lambda u: (u.first_name.lower(), u.last_name.lower()))
    return [{**user_summary(u), "details": {}} for u in users]


@router.post("/", status_code=201)
def admin_register_user(
    dto: UserRegisterDTO,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """El admin registra estudiantes o instructores (Abstract Factory)."""
    if getattr(dto.role, "value", dto.role) not in MANAGEABLE_ROLES:
        raise HTTPException(
            status_code=400,
            detail="El administrador solo puede registrar estudiantes o instructores.",
        )
    repo = SqlAlchemyUserRepository(db)
    try:
        created = RegisterUserUseCase(repo).execute(dto)
    except EmailAlreadyRegisteredError:
        raise HTTPException(status_code=409, detail="El correo ya está registrado.")
    return user_summary(repo.get_by_id(created.user_id))


@router.get("/{user_id}/detail")
def user_detail(
    user_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Ficha completa: cursos inscritos (sin iniciar/iniciado/terminado),
    certificados y pagos del estudiante, o cursos y alumnos del instructor."""
    try:
        return _detail_service(db).get(user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")


@router.patch("/{user_id}/status")
def set_user_status(
    user_id: str,
    dto: UserStatusDTO,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """Suspende (`is_active=false`) o reactiva un estudiante o instructor.
    Efecto inmediato: sus tokens dejan de servir y no puede iniciar sesión."""
    use_case = SetUserStatusUseCase(SqlAlchemyUserRepository(db))
    try:
        return use_case.execute(user_id, is_active=dto.is_active, acting_admin_id=admin.id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    except UserStatusNotAllowedError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """Elimina un estudiante o instructor (irreversible). No elimina admins ni
    la propia cuenta (400). Un instructor con cursos -> 409 (suspéndelo). Al
    estudiante se le quita de sus inscripciones; pagos y certificados quedan
    como historial."""
    use_case = DeleteUserUseCase(SqlAlchemyUserRepository(db), container.course_repository)
    try:
        return use_case.execute(user_id, acting_admin_id=admin.id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    except UserStatusNotAllowedError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except UserHasCoursesError as error:
        raise HTTPException(status_code=409, detail=str(error))

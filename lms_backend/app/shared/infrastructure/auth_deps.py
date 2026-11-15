"""Dependencias de autenticación/autorización reutilizables por todos los routers.

- get_current_user: resuelve el usuario a partir de 'Authorization: Bearer <token>'
  (401 si falta el token o la sesión no es válida).
- require_role(*roles): exige que el usuario autenticado tenga uno de los roles
  indicados (403 si no lo tiene).
"""

from typing import Callable

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.modules.auth.infrastructure.security import resolve_token
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Resuelve el usuario a partir de 'Authorization: Bearer <token>'."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    user_id = resolve_token(authorization[7:].strip())
    user = SqlAlchemyUserRepository(db).get_by_id(user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=401, detail="Sesión no válida")
    return user


def require_role(*roles: str) -> Callable:
    """Fábrica de dependencias: permite el acceso solo a los roles dados."""
    allowed = {str(getattr(role, "value", role)) for role in roles}

    def _dependency(user=Depends(get_current_user)):
        if user.role not in allowed:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para realizar esta acción.",
            )
        return user

    return _dependency

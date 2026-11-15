"""Traducción única de errores de dominio/aplicación a respuestas HTTP.

- InvalidStateTransition -> 409 (transición de estado inválida)
- ResourceNotFound       -> 404
- PermissionDenied       -> 403
- ValueError             -> 422 (validación de reglas del dominio)
Los errores adicionales del módulo (p. ej. límite de intentos -> 409) se
pasan en `extra`.
"""

from contextlib import contextmanager
from typing import Dict, Iterator, Optional, Type

from fastapi import HTTPException

from app.shared.domain.errors import PermissionDenied, ResourceNotFound
from app.shared.domain.state import InvalidStateTransition

_BASE: Dict[Type[Exception], int] = {
    InvalidStateTransition: 409,
    ResourceNotFound: 404,
    PermissionDenied: 403,
    ValueError: 422,
}


@contextmanager
def domain_errors_as_http(
    extra: Optional[Dict[Type[Exception], int]] = None,
) -> Iterator[None]:
    mapping = {**(extra or {}), **_BASE}
    try:
        yield
    except tuple(mapping) as error:  # type: ignore[misc]
        status = next(code for exc, code in mapping.items() if isinstance(error, exc))
        raise HTTPException(status_code=status, detail=str(error)) from error

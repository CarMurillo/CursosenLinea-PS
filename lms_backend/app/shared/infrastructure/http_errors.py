"""Traducción única de errores de dominio/aplicación a respuestas HTTP.

- InvalidStateTransition -> 409 (transición de estado inválida)
- ResourceNotFound       -> 404
- PermissionDenied       -> 403
- ValueError             -> 422 (validación de reglas del dominio)
Los errores adicionales del módulo (p. ej. límite de intentos -> 409) se
pasan en `extra`.

`request_validation_error_handler` (registrado en main.py) devuelve el 422
de validación de entrada con un cuerpo siempre serializable.
"""

import math
from contextlib import contextmanager
from typing import Dict, Iterator, Optional, Type

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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


def _json_safe(value):
    """Reemplaza floats no finitos (inf/NaN) por su texto: JSON no los admite."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


async def request_validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """422 como el de FastAPI, pero serializable aunque la entrada traiga
    Infinity/NaN (p. ej. `{"price": 1e999}`): sin esto la respuesta de error
    fallaba al serializar `input: inf` y terminaba en 500."""
    return JSONResponse(
        status_code=422,
        content={"detail": _json_safe(jsonable_encoder(exc.errors()))},
    )

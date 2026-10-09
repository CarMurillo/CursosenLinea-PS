
"""Utilidades de seguridad para el módulo de autenticación.

Fase actual del proyecto: hashing real de contraseñas (PBKDF2) y tokens
de sesión opacos guardados en memoria del proceso. Se aislaron detrás
de funciones simples a propósito: en una fase posterior se puede
cambiar la implementación de tokens por JWT firmado sin tocar los
casos de uso ni los endpoints que las consumen.
"""

import hashlib
import hmac
import secrets
from typing import Optional

_PBKDF2_ITERATIONS = 100_000

# Mapa token -> user_id. Es una solución simplificada válida para esta
# fase del curso (proceso único, sin múltiples réplicas del backend).
_active_tokens: dict[str, str] = {}


def hash_password(plain_password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
    )
    return f"{salt}${digest.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, digest_hex = hashed_password.split("$")
    except ValueError:
        return False
    new_digest = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
    )
    return hmac.compare_digest(new_digest.hex(), digest_hex)


def issue_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    _active_tokens[token] = user_id
    return token


def resolve_token(token: str) -> Optional[str]:
    return _active_tokens.get(token)
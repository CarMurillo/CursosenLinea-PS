"""Errores de aplicación genéricos (la capa HTTP los traduce a 404/403)."""


class ResourceNotFound(Exception):
    """El recurso no existe o no es visible para quien lo pide (404)."""


class PermissionDenied(Exception):
    """El usuario está autenticado pero no puede hacer la operación (403)."""

"""
Piezas compartidas por las máquinas de estado (patrón State, GoF).

- `InvalidStateTransition`: error de dominio que lanza un estado concreto
  cuando la operación pedida no está permitida en él. La capa HTTP lo
  traduce a 409 Conflict.
- `CourseInfo` / `CourseCatalogPort`: vista mínima de un curso que necesitan
  los módulos de evaluaciones, clases en vivo y certificados, sin depender
  del módulo `courses` (el composition root inyecta el adaptador).

Dominio puro: sin FastAPI ni SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Optional, Protocol


class InvalidStateTransition(Exception):
    """La operación `action` no está permitida en el estado `state`."""

    def __init__(self, entity: str, state: str, action: str, detail: str = ""):
        self.entity = entity
        self.state = state
        self.action = action
        message = (
            f"No se puede '{action}' {entity} en estado '{state}'."
            + (f" {detail}" if detail else "")
        )
        super().__init__(message)


@dataclass(frozen=True)
class CourseInfo:
    course_id: str
    title: str
    instructor_id: Optional[str]
    enrolled_students: FrozenSet[str] = field(default_factory=frozenset)
    has_certificate: bool = False

    def is_managed_by(self, user_id: str, role: str) -> bool:
        """Dueño del curso o administrador."""
        return role == "admin" or (
            self.instructor_id is not None and self.instructor_id == user_id
        )

    def is_enrolled(self, user_id: str) -> bool:
        return user_id in self.enrolled_students


class CourseCatalogPort(Protocol):
    def get_course_info(self, course_id: str) -> Optional[CourseInfo]: ...

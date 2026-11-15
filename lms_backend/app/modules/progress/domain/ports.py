"""
Módulo: Progress - Puerto del dominio (arquitectura hexagonal).

El progreso de un estudiante es estado EXTRÍNSECO respecto al contenido del
curso: las lecciones (y sus metadatos Flyweight) se comparten entre todos los
estudiantes; lo que cambia por estudiante son los lesson_id completados, que
se guardan aquí y se entregan al ProgressVisitor al recorrer el Composite.
"""

from abc import ABC, abstractmethod


class ProgressRepository(ABC):
    """(user_id, course_id) -> conjunto de lesson_id completados."""

    @abstractmethod
    def mark_completed(self, user_id: str, course_id: str, lesson_id: str) -> bool:
        """Registra la lección como completada. Idempotente.

        Devuelve True si se registró ahora y False si ya estaba completada.
        """

    @abstractmethod
    def completed_lessons(self, user_id: str, course_id: str) -> set[str]:
        """Copia del conjunto de lesson_id completados por el usuario en el curso."""

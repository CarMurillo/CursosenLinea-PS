"""
Casos de uso del progreso por estudiante (Visitor + Proxy + Composite).

El contenido llega como `ContentComponent` (normalmente un
ProtectedContentProxy): si el usuario no tiene acceso, el proxy lanza
ContentAccessDenied al aceptar el visitante y el caso de uso no registra nada.
"""

from typing import Any, Callable, Optional

from app.modules.courses.domain.content_component import ContentComponent
from app.modules.courses.domain.visitor import LessonIndexVisitor, ProgressVisitor
from app.modules.progress.domain.ports import ProgressRepository


class LessonNotFoundError(Exception):
    """La lección no existe en el contenido del curso (HTTP 404)."""


class CompleteLessonUseCase:
    """
    Marca una lección como completada (idempotente) y devuelve el progreso.

    Punto de enganche Observer: si se inyectan `event_bus` y `event_factory`
    se publica un evento LESSON_COMPLETED solo la primera vez que se completa
    la lección. `event_factory(user_id=..., course_id=..., lesson_id=...,
    progress=...)` construye el DomainEvent; así este módulo no depende del
    módulo de eventos (lo cablea el composition root).
    """

    def __init__(
        self,
        progress_repository: ProgressRepository,
        event_bus: Optional[Any] = None,
        event_factory: Optional[Callable[..., Any]] = None,
    ):
        self._progress = progress_repository
        self.event_bus = event_bus
        self.event_factory = event_factory

    def execute(
        self,
        content: ContentComponent,
        user_id: str,
        course_id: str,
        lesson_id: str,
    ) -> dict:
        index = LessonIndexVisitor()
        content.accept(index)          # Proxy: puede lanzar ContentAccessDenied
        if not index.contains(lesson_id):
            raise LessonNotFoundError(lesson_id)

        newly = self._progress.mark_completed(user_id, course_id, lesson_id)

        progress = ProgressVisitor(
            self._progress.completed_lessons(user_id, course_id)
        )
        content.accept(progress)
        result = progress.result()

        if newly and self.event_bus is not None and self.event_factory is not None:
            self.event_bus.notify(
                self.event_factory(
                    user_id=user_id,
                    course_id=course_id,
                    lesson_id=lesson_id,
                    progress=result,
                )
            )

        return {
            "lesson_id": lesson_id,
            "already_completed": not newly,
            "progress": result,
        }


class GetProgressUseCase:
    """Progreso del estudiante en un curso, calculado con ProgressVisitor."""

    def __init__(self, progress_repository: ProgressRepository):
        self._progress = progress_repository

    def execute(self, content: ContentComponent, user_id: str, course_id: str) -> dict:
        visitor = ProgressVisitor(self._progress.completed_lessons(user_id, course_id))
        content.accept(visitor)
        return visitor.result()

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # solo para anotaciones; evita importaciones circulares
    from app.modules.courses.domain.composite import LessonModule
    from app.modules.courses.domain.visitor import ContentVisitor


class ContentComponent(ABC):
    """
    Componente común utilizado por el patrón Composite.

    Visitor: cada componente implementa `accept(visitor)` (doble despacho),
    de modo que las operaciones sobre el árbol (duración, progreso, temario)
    viven en visitantes y el cliente nunca pregunta por el tipo concreto.
    """

    @abstractmethod
    def render_content(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def accept(self, visitor: "ContentVisitor") -> Any:
        """Doble despacho: el componente llama al método visit_* que le corresponde."""

    def as_module(self) -> Optional["LessonModule"]:
        """
        Devuelve el componente como módulo si puede contener hijos.

        Las hojas (lecciones) devuelven None; LessonModule se devuelve a sí
        mismo. Sustituye a `isinstance(child, LessonModule)` en el Composite.
        """
        return None

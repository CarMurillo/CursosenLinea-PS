from typing import TYPE_CHECKING, Any

from app.modules.courses.domain.content_component import (
    ContentComponent
)

if TYPE_CHECKING:
    from app.modules.courses.domain.visitor import ContentVisitor


class LessonModule(ContentComponent):
    """
    Composite.

    Puede contener diferentes componentes de contenido.
    """

    def __init__(self, title: str):

        self.title = title

        self._children: list[
            ContentComponent
        ] = []


    def add(
        self,
        component: ContentComponent
    ) -> None:

        self._children.append(component)


    def remove(
        self,
        component: ContentComponent
    ) -> None:

        self._children.remove(component)


    def render_content(self) -> str:

        rendered_children = [
            child.render_content()
            for child in self._children
        ]

        return (
            f"Módulo: {self.title}\n"
            + "\n".join(rendered_children)
        )


    def to_dict(self) -> dict:

        return {
            "title": self.title,
            "items": [
                child.to_dict()
                for child in self._children
            ],
        }


    def as_module(self) -> "LessonModule":

        return self


    def _accept_children(self, visitor: "ContentVisitor") -> None:

        for child in self._children:
            child.accept(visitor)


    def accept(self, visitor: "ContentVisitor") -> Any:
        """VISITOR: visita el módulo y luego recorre sus hijos."""

        visitor.visit_module(self)
        self._accept_children(visitor)
        visitor.leave_module(self)
        return visitor


class CourseContent(LessonModule):
    """
    Composite raíz.

    Representa todo el contenido de un curso.
    """

    def __init__(
        self,
        course_title: str
    ):

        super().__init__(
            f"Contenido de {course_title}"
        )


    def accept(self, visitor: "ContentVisitor") -> Any:
        """
        VISITOR: la raíz no cuenta como módulo del temario; avisa al
        visitante con visit_course/leave_course y recorre los hijos.
        """

        visitor.visit_course(self)
        self._accept_children(visitor)
        visitor.leave_course(self)
        return visitor


    def add_module(
        self,
        module_title: str
    ) -> LessonModule:

        module = LessonModule(
            module_title
        )

        self.add(module)

        return module


    def find_module(
        self,
        module_title: str
    ) -> LessonModule | None:

        # Polimorfismo (as_module) en lugar de isinstance.
        for child in self._children:

            module = child.as_module()

            if (
                module is not None
                and module.title == module_title
            ):
                return module

        return None


    def add_lesson(
        self,
        module_title: str,
        lesson: ContentComponent
    ) -> None:

        module = self.find_module(
            module_title
        )

        if module is None:

            module = self.add_module(
                module_title
            )

        module.add(lesson)

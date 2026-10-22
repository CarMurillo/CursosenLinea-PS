
from app.modules.courses.domain.content_component import (
    ContentComponent
)


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

        for child in self._children:

            if (
                isinstance(
                    child,
                    LessonModule
                )
                and child.title == module_title
            ):
                return child

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
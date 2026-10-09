"""
Patrón de Diseño: Builder

Construye progresivamente un curso del LMS y utiliza el Factory Method
para crear el tipo concreto de curso.
"""

import uuid
from typing import Optional

from app.modules.courses.domain.models import Course, CourseFactory


class CourseBuilder:
    """
    Builder para construir cursos del LMS paso a paso.

    El Builder se encarga de preparar los datos del curso.
    El Factory Method se encarga de decidir qué tipo concreto crear.
    """

    def __init__(self):
        self._course_id: str = str(uuid.uuid4())
        self._title: Optional[str] = None
        self._instructor: Optional[str] = None
        self._price: float = 0.0
        self._course_type: str = "video"

    def set_title(self, title: str) -> "CourseBuilder":
        if not title or not title.strip():
            raise ValueError("El título del curso no puede estar vacío.")

        self._title = title.strip()
        return self

    def set_instructor(self, instructor: str) -> "CourseBuilder":
        if not instructor or not instructor.strip():
            raise ValueError("El instructor es obligatorio.")

        self._instructor = instructor.strip()
        return self

    def set_price(self, price: float) -> "CourseBuilder":
        if price < 0:
            raise ValueError("El precio no puede ser negativo.")

        self._price = price
        return self

    def set_course_type(self, course_type: str) -> "CourseBuilder":
        if course_type not in ("video", "live"):
            raise ValueError(
                "El tipo de curso debe ser 'video' o 'live'."
            )

        self._course_type = course_type
        return self

    def build(self) -> Course:
        """
        Construye el curso utilizando el Factory Method.
        """

        if not self._title:
            raise ValueError("El título es obligatorio.")

        if not self._instructor:
            raise ValueError("El instructor es obligatorio.")

        return CourseFactory.create_course(
            course_type=self._course_type,
            course_id=self._course_id,
            title=self._title,
            instructor=self._instructor,
            price=self._price,
        )
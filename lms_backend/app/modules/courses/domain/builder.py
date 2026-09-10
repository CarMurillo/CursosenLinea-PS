"""
Módulo: Courses - Capa de Dominio (Domain)
Patrón de Diseño: Builder (Creacional)
"""

from typing import List, Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class Lesson:
    id: str
    title: str
    content: str
    duration_minutes: int


@dataclass
class Module:
    id: str
    title: str
    lessons: List[Lesson] = field(default_factory=list)


@dataclass
class Course:
    id: str
    title: str
    description: str
    instructor_id: str
    category: str
    price: float
    is_published: bool
    modules: List[Module] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class CourseBuilder:
    """
    Builder concreto para construir instancias válidas de Course.
    Cumple con SRP al separar la construcción de la entidad.
    """

    def __init__(self, title: str, instructor_id: str):
        self._id: str = str(uuid.uuid4())
        self._title: str = title
        self._instructor_id: str = instructor_id
        self._description: str = ""
        self._category: str = "General"
        self._price: float = 0.0
        self._is_published: bool = False
        self._modules: List[Module] = []
        self._tags: List[str] = []

    def set_description(self, description: str) -> 'CourseBuilder':
        self._description = description
        return self

    def set_category(self, category: str) -> 'CourseBuilder':
        self._category = category
        return self

    def set_price(self, price: float) -> 'CourseBuilder':
        if price < 0:
            raise ValueError("El precio no puede ser negativo.")
        self._price = price
        return self

    def set_published(self, is_published: bool) -> 'CourseBuilder':
        self._is_published = is_published
        return self

    def add_tag(self, tag: str) -> 'CourseBuilder':
        if tag not in self._tags:
            self._tags.append(tag)
        return self

    def add_module(self, title: str, lessons: Optional[List[dict]] = None) -> 'CourseBuilder':
        module_id = str(uuid.uuid4())
        module_lessons = []
        if lessons:
            for l in lessons:
                lesson_obj = Lesson(
                    id=str(uuid.uuid4()),
                    title=l.get("title", "Lección sin título"),
                    content=l.get("content", ""),
                    duration_minutes=l.get("duration_minutes", 0)
                )
                module_lessons.append(lesson_obj)
        
        new_module = Module(id=module_id, title=title, lessons=module_lessons)
        self._modules.append(new_module)
        return self

    def build(self) -> Course:
        """Valida y retorna la instancia final de Course."""
        if not self._title.strip():
            raise ValueError("El título del curso no puede estar vacío.")
        
        return Course(
            id=self._id,
            title=self._title,
            description=self._description,
            instructor_id=self._instructor_id,
            category=self._category,
            price=self._price,
            is_published=self._is_published,
            modules=self._modules,
            tags=self._tags
        )
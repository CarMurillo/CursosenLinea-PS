from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.courses.domain.models import Course


class CourseRepository(ABC):
    """Puerto del dominio de cursos (arquitectura hexagonal)."""

    @abstractmethod
    def save(self, course: Course) -> Course:
        pass

    @abstractmethod
    def get_by_id(self, course_id: str) -> Optional[Course]:
        pass

    @abstractmethod
    def list_all(self) -> List[Course]:
        pass
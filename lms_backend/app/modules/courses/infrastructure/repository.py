from typing import Dict, List, Optional

from app.modules.courses.domain.models import Course
from app.modules.courses.domain.ports import CourseRepository


class InMemoryCourseRepository(CourseRepository):
    """Adaptador en memoria para esta fase del proyecto.

    Implementa el puerto CourseRepository, así que puede reemplazarse
    después por un adaptador con SQLAlchemy sin tocar el dominio ni los
    casos de uso (esa es justamente la ventaja de la arquitectura
    hexagonal).
    """

    def __init__(self):
        self._courses: Dict[str, Course] = {}

    def save(self, course: Course) -> Course:
        self._courses[course.course_id] = course
        return course

    def get_by_id(self, course_id: str) -> Optional[Course]:
        return self._courses.get(course_id)

    def list_all(self) -> List[Course]:
        return list(self._courses.values())


# Instancia compartida por toda la app durante esta fase (sin persistencia real todavía).
course_repository = InMemoryCourseRepository()
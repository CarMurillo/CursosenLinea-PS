from abc import ABC, abstractmethod
from typing import List


# --- Entidad Base / Abstracción ---
class Course(ABC):
    def __init__(self, course_id: str, title: str, instructor: str, price: float):
        self.course_id = course_id
        self.title = title
        self.instructor = instructor
        self.price = price
        self.enrolled_students: List[str] = []

    @abstractmethod
    def get_course_type(self) -> str:
        pass

    @abstractmethod
    def get_details(self) -> dict:
        pass


# --- Productos Concretos ---
class VideoCourse(Course):
    def get_course_type(self) -> str:
        return "Video bajo demanda"

    def get_details(self) -> dict:
        return {
            "id": self.course_id,
            "title": self.title,
            "instructor": self.instructor,
            "price": self.price,
            "type": self.get_course_type(),
            "badge": "bg-primary"
        }


class LiveClassCourse(Course):
    def get_course_type(self) -> str:
        return "Clase en Vivo (Videoconferencia)"

    def get_details(self) -> dict:
        return {
            "id": self.course_id,
            "title": self.title,
            "instructor": self.instructor,
            "price": self.price,
            "type": self.get_course_type(),
            "badge": "bg-danger"
        }


# --- PATRÓN GOF: FACTORY METHOD ---
class CourseFactory:
    """Fábrica para instanciar tipos de cursos sin acoplar el código cliente."""
    
    @staticmethod
    def create_course(course_type: str, course_id: str, title: str, instructor: str, price: float) -> Course:
        if course_type.lower() == "video":
            return VideoCourse(course_id, title, instructor, price)
        elif course_type.lower() == "live":
            return LiveClassCourse(course_id, title, instructor, price)
        else:
            raise ValueError(f"Tipo de curso desconocido: {course_type}")
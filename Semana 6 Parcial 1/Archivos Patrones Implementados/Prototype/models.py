from abc import ABC, abstractmethod
from copy import deepcopy
from typing import List
import uuid


# ============================================================
# ENTIDAD BASE
# ============================================================

class Course(ABC):

    def __init__(
        self,
        course_id: str,
        title: str,
        instructor: str,
        price: float
    ):
        self.course_id = course_id
        self.title = title
        self.instructor = instructor
        self.price = price
        self.enrolled_students: List[str] = []

    # ========================================================
    # PATRÓN PROTOTYPE
    # ========================================================

    def clone(self) -> "Course":
        """
        Crea una copia independiente del curso actual.

        Se utiliza deepcopy para evitar que la copia comparta
        listas u otros objetos mutables con el curso original.
        """

        cloned_course = deepcopy(self)

        # El clon debe ser un curso diferente.
        cloned_course.course_id = str(uuid.uuid4())

        # Los estudiantes inscritos no se copian.
        # El nuevo curso comienza sin matrículas.
        cloned_course.enrolled_students = []

        return cloned_course

    # ========================================================
    # FACTORY METHOD
    # ========================================================

    @abstractmethod
    def get_course_type(self) -> str:
        pass

    @abstractmethod
    def get_details(self) -> dict:
        pass


# ============================================================
# PRODUCTO CONCRETO: VIDEO
# ============================================================

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


# ============================================================
# PRODUCTO CONCRETO: CLASE EN VIVO
# ============================================================

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


# ============================================================
# PATRÓN FACTORY METHOD
# ============================================================

class CourseFactory:
    """
    Factory Method encargado de crear el tipo concreto de curso.
    """

    @staticmethod
    def create_course(
        course_type: str,
        course_id: str,
        title: str,
        instructor: str,
        price: float
    ) -> Course:

        if course_type.lower() == "video":

            return VideoCourse(
                course_id,
                title,
                instructor,
                price
            )

        elif course_type.lower() == "live":

            return LiveClassCourse(
                course_id,
                title,
                instructor,
                price
            )

        else:
            raise ValueError(
                f"Tipo de curso desconocido: {course_type}"
            )
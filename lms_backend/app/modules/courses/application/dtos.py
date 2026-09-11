from typing import Literal, Optional

from pydantic import BaseModel, Field


class CourseCreateDTO(BaseModel):
    title: str
    instructor: str
    price: float = Field(ge=0)
    course_type: Literal["video", "live"]


class EnrollmentDTO(BaseModel):
    student_name: str


class CloneCourseDTO(BaseModel):
    """
    Datos opcionales para personalizar el curso clonado.
    """

    new_title: Optional[str] = None
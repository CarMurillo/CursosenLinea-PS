from typing import Literal, Optional

from pydantic import BaseModel, Field


class CourseCreateDTO(BaseModel):

    title: str

    # Compatibilidad: el instructor real se deriva del token en la API.
    # Si llega en el cuerpo se ignora en el endpoint HTTP.
    instructor: Optional[str] = None

    price: float = Field(
        ge=0
    )

    course_type: Literal[
        "video",
        "live"
    ]

    premium: bool = False

    certificate: bool = False


class EnrollmentDTO(BaseModel):
    """Cuerpo opcional y obsoleto: la identidad sale del token.

    Se conserva `student_name` solo por compatibilidad con clientes
    antiguos; el endpoint lo ignora.
    """

    student_name: Optional[str] = None


class CloneCourseDTO(BaseModel):

    new_title: Optional[str] = None


class LessonCreateDTO(BaseModel):

    module_title: str = Field(
        min_length=1
    )

    title: str = Field(
        min_length=1
    )

    media_id: str = Field(
        min_length=1
    )

    provider: Literal[
        "vimeo",
        "s3"
    ]

    lesson_type: Literal[
        "video",
        "quiz"
    ] = "video"

    # Opcional: si no llega se usa la duración por defecto (10 minutos).
    duration_minutes: Optional[int] = Field(
        default=None,
        gt=0,
    )
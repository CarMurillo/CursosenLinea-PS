from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.shared.application.dtos import MAX_MONEY_AMOUNT, StrictDTO


class CourseCreateDTO(StrictDTO):

    title: str

    # Compatibilidad: el instructor real se deriva del token en la API.
    # Si llega en el cuerpo se ignora en el endpoint HTTP.
    instructor: Optional[str] = None

    # StrictDTO rechaza Infinity/NaN (422) y `le` acota el precio.
    price: float = Field(
        ge=0,
        le=MAX_MONEY_AMOUNT,
    )

    course_type: Literal[
        "video",
        "live"
    ]

    premium: bool = False

    certificate: bool = False

    @model_validator(mode="after")
    def _premium_requires_price(self) -> "CourseCreateDTO":
        # Un curso Premium con precio 0 no se puede adquirir (el pago exige
        # amount > 0 y la inscripción exige pago aprobado): se rechaza (422).
        if self.premium and self.price <= 0:
            raise ValueError("Un curso Premium requiere un precio mayor que 0.")
        return self


class EnrollmentDTO(BaseModel):
    """Cuerpo opcional y obsoleto: la identidad sale del token.

    Se conserva `student_name` solo por compatibilidad con clientes
    antiguos; el endpoint lo ignora.
    """

    student_name: Optional[str] = None


class CloneCourseDTO(BaseModel):

    new_title: Optional[str] = None


class LessonCreateDTO(StrictDTO):

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
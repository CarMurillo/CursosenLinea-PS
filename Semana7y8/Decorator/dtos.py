from typing import Literal, Optional

from pydantic import BaseModel, Field


class CourseCreateDTO(BaseModel):

    title: str

    instructor: str

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

    student_name: str


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
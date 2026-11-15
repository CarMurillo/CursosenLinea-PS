from typing import Dict, List

from pydantic import BaseModel, Field


class AssessmentCreateDTO(BaseModel):
    course_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    passing_score: float = Field(default=60.0, ge=0, le=100)
    max_attempts: int = Field(default=1, ge=1, le=20)


class QuestionCreateDTO(BaseModel):
    text: str = Field(min_length=1)
    options: List[str] = Field(min_length=2, max_length=10)
    correct_option: int = Field(ge=0)
    points: float = Field(default=1.0, gt=0)


class AttemptSubmitDTO(BaseModel):
    # question_id -> índice de la opción elegida (0-based).
    answers: Dict[str, int] = Field(default_factory=dict)

from typing import Dict, List

from pydantic import Field, field_validator

from app.shared.application.dtos import StrictDTO


class AssessmentCreateDTO(StrictDTO):
    course_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    passing_score: float = Field(default=60.0, ge=0, le=100)
    max_attempts: int = Field(default=1, ge=1, le=20)


class QuestionCreateDTO(StrictDTO):
    text: str = Field(min_length=1)
    options: List[str] = Field(min_length=2, max_length=10)
    correct_option: int = Field(ge=0)
    points: float = Field(default=1.0, gt=0, le=1000)

    @field_validator("options")
    @classmethod
    def _options_not_blank_nor_duplicated(cls, options: List[str]) -> List[str]:
        cleaned = [option.strip() for option in options]
        if any(not option for option in cleaned):
            raise ValueError("Las opciones no pueden estar vacías.")
        if len({option.casefold() for option in cleaned}) != len(cleaned):
            raise ValueError("Las opciones no pueden repetirse.")
        return cleaned


class AttemptSubmitDTO(StrictDTO):
    # question_id -> índice de la opción elegida (0-based).
    answers: Dict[str, int] = Field(default_factory=dict)

"""
Entidades de evaluaciones. `Assessment` es el CONTEXTO del patrón State.

Las operaciones públicas (`add_question`, `publish`, `submit_attempt`,
`close`) delegan siempre en `self._state`. Los métodos con guion bajo son
las operaciones primitivas que solo invocan los estados concretos.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Mapping, Optional

from app.modules.assessments.domain.states import AssessmentState, DraftState


class AttemptLimitReached(Exception):
    """El estudiante ya agotó los intentos permitidos."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Question:
    """Pregunta de opción múltiple con una única respuesta correcta."""

    text: str
    options: List[str]
    correct_option: int
    points: float = 1.0
    question_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise ValueError("La pregunta necesita un enunciado.")
        if len(self.options) < 2:
            raise ValueError("La pregunta necesita al menos 2 opciones.")
        if not 0 <= self.correct_option < len(self.options):
            raise ValueError("correct_option fuera del rango de opciones.")
        if self.points <= 0:
            raise ValueError("El puntaje de la pregunta debe ser mayor que 0.")

    def score_for(self, selected: Optional[int]) -> float:
        return self.points if selected == self.correct_option else 0.0

    def to_dict(self, include_answer: bool = True) -> dict:
        data = {
            "question_id": self.question_id,
            "text": self.text,
            "options": list(self.options),
            "points": self.points,
        }
        if include_answer:
            data["correct_option"] = self.correct_option
        return data


@dataclass
class Attempt:
    assessment_id: str
    user_id: str
    answers: Dict[str, int]
    score: float
    max_score: float
    percentage: float
    passed: bool
    attempt_number: int
    attempt_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    submitted_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "attempt_id": self.attempt_id,
            "assessment_id": self.assessment_id,
            "user_id": self.user_id,
            "answers": dict(self.answers),
            "score": self.score,
            "max_score": self.max_score,
            "percentage": self.percentage,
            "passed": self.passed,
            "attempt_number": self.attempt_number,
            "submitted_at": self.submitted_at.isoformat(),
        }


class Assessment:
    """Contexto del patrón State.

    `passing_score` es el porcentaje mínimo (0-100) del puntaje máximo para
    aprobar. `max_attempts` limita los intentos por estudiante.
    """

    def __init__(
        self,
        course_id: str,
        title: str,
        *,
        created_by: str,
        passing_score: float = 60.0,
        max_attempts: int = 1,
        description: str = "",
        assessment_id: Optional[str] = None,
        state: Optional[AssessmentState] = None,
    ):
        if not title or not title.strip():
            raise ValueError("La evaluación necesita un título.")
        if not 0 <= passing_score <= 100:
            raise ValueError("passing_score debe estar entre 0 y 100.")
        if max_attempts < 1:
            raise ValueError("max_attempts debe ser al menos 1.")
        self.assessment_id = assessment_id or str(uuid.uuid4())
        self.course_id = course_id
        self.title = title.strip()
        self.description = description
        self.created_by = created_by
        self.passing_score = float(passing_score)
        self.max_attempts = max_attempts
        self.questions: List[Question] = []
        self.attempts: List[Attempt] = []
        self.created_at = _now()
        self._state: AssessmentState = state or DraftState()

    # ------------------------------------------------- delegación al estado
    @property
    def state(self) -> AssessmentState:
        return self._state

    @property
    def state_name(self) -> str:
        return self._state.name

    @property
    def visible_to_students(self) -> bool:
        return self._state.visible_to_students

    def add_question(self, question: Question) -> Question:
        self._state.add_question(self, question)
        return question

    def publish(self) -> None:
        self._state.publish(self)

    def submit_attempt(self, user_id: str, answers: Mapping[str, int]) -> Attempt:
        return self._state.submit_attempt(self, user_id, answers)

    def close(self) -> None:
        self._state.close(self)

    # -------------------------------------- primitivas (las usan los estados)
    def _transition_to(self, state: AssessmentState) -> None:
        self._state = state

    def _append_question(self, question: Question) -> None:
        self.questions.append(question)

    def _grade_and_record(self, user_id: str, answers: Mapping[str, int]) -> Attempt:
        """Calificación automática + registro del intento."""
        if len(self.attempts_of(user_id)) >= self.max_attempts:
            raise AttemptLimitReached(
                f"Ya usaste los {self.max_attempts} intento(s) permitidos."
            )
        by_id = {q.question_id: q for q in self.questions}
        unknown = set(answers) - set(by_id)
        if unknown:
            raise ValueError(f"Preguntas desconocidas: {sorted(unknown)}")

        score = sum(q.score_for(answers.get(q.question_id)) for q in self.questions)
        max_score = self.max_score
        percentage = round(score * 100 / max_score, 2) if max_score else 0.0
        attempt = Attempt(
            assessment_id=self.assessment_id,
            user_id=user_id,
            answers=dict(answers),
            score=score,
            max_score=max_score,
            percentage=percentage,
            passed=percentage >= self.passing_score,
            attempt_number=len(self.attempts_of(user_id)) + 1,
        )
        self.attempts.append(attempt)
        return attempt

    # ------------------------------------------------------------- consultas
    @property
    def max_score(self) -> float:
        return float(sum(q.points for q in self.questions))

    def attempts_of(self, user_id: str) -> List[Attempt]:
        return [a for a in self.attempts if a.user_id == user_id]

    def to_dict(self, include_answers: bool = True) -> dict:
        return {
            "id": self.assessment_id,
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description,
            "state": self.state_name,
            "passing_score": self.passing_score,
            "max_attempts": self.max_attempts,
            "max_score": self.max_score,
            "question_count": len(self.questions),
            "questions": [q.to_dict(include_answers) for q in self.questions],
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }

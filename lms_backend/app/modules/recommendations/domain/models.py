"""Modelos del dominio de recomendaciones (dominio puro, sin frameworks).

- `CourseSnapshot`: vista de solo lectura de un curso del catálogo.
- `LearnerProfile`: lo que sabemos del estudiante (inscripciones, progreso
  calculado con el Visitor, notas de evaluaciones y certificados).
- `Recommendation`: sugerencia con su motivo (`reason`) legible.
"""

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Tuple


@dataclass(frozen=True)
class CourseSnapshot:
    course_id: str
    title: str
    instructor: str = ""
    instructor_id: Optional[str] = None
    course_type: str = ""
    price: float = 0.0
    premium: bool = False
    has_certificate: bool = False
    enrolled_count: int = 0

    @property
    def is_free(self) -> bool:
        return not self.premium and float(self.price or 0) <= 0


@dataclass(frozen=True)
class AssessmentResult:
    course_id: str
    assessment_id: Optional[str]
    score: Optional[float]
    passed: bool


@dataclass(frozen=True)
class LearnerProfile:
    user_id: str
    enrolled_course_ids: FrozenSet[str] = frozenset()
    # course_id -> % de avance (0..100) calculado con ProgressVisitor.
    progress: Dict[str, float] = field(default_factory=dict)
    assessments: Tuple[AssessmentResult, ...] = ()
    certificate_course_ids: FrozenSet[str] = frozenset()

    @property
    def is_newcomer(self) -> bool:
        return not self.enrolled_course_ids

    def failed_course_ids(self) -> List[str]:
        """Cursos con alguna evaluación reprobada y ninguna aprobada."""
        passed = {a.course_id for a in self.assessments if a.passed}
        seen: List[str] = []
        for a in self.assessments:
            if not a.passed and a.course_id not in passed and a.course_id not in seen:
                seen.append(a.course_id)
        return seen

    def active_course_ids(self) -> List[str]:
        """Cursos con progreso > 0 (los más avanzados primero)."""
        return [
            cid for cid, pct in sorted(self.progress.items(), key=lambda kv: -kv[1])
            if pct > 0
        ]


@dataclass(frozen=True)
class Recommendation:
    course_id: str
    title: str
    reason: str
    rule: str
    score: float

    def to_dict(self) -> dict:
        return {
            "course_id": self.course_id,
            "title": self.title,
            "reason": self.reason,
            "rule": self.rule,
            "score": self.score,
        }

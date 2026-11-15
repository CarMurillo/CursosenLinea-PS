"""Caso de uso: recomendaciones personalizadas por reglas.

Combina tres entradas:
- perfil de aprendizaje (lo alimenta RecommendationProfileObserver con
  STUDENT_ENROLLED, LESSON_COMPLETED, ASSESSMENT_GRADED, CERTIFICATE_ISSUED);
- inscripciones reales del catálogo (fuente de verdad para excluir cursos);
- progreso por curso calculado con ProgressVisitor (puerto ProgressReaderPort).
"""

from typing import List, Optional

from app.modules.recommendations.domain.models import AssessmentResult, LearnerProfile
from app.modules.recommendations.domain.ports import (
    LearningProfilePort,
    ProgressReaderPort,
    RecommendationCatalogPort,
)
from app.modules.recommendations.domain.strategies import RecommendationEngine


class GetRecommendationsUseCase:
    def __init__(
        self,
        profiles: LearningProfilePort,
        catalog: RecommendationCatalogPort,
        progress: ProgressReaderPort,
        engine: Optional[RecommendationEngine] = None,
    ):
        self._profiles = profiles
        self._catalog = catalog
        self._progress = progress
        self._engine = engine or RecommendationEngine()

    def build_profile(self, user_id: str) -> LearnerProfile:
        raw = self._profiles.get_profile(user_id)
        enrolled = set(raw.get("enrolled_courses", [])) | set(
            self._catalog.enrolled_course_ids(user_id)
        )
        tracked = enrolled | set(raw.get("completed_lessons", {}).keys())
        progress = {
            cid: self._progress.progress_percent(user_id, cid) for cid in sorted(tracked)
        }
        assessments = tuple(
            AssessmentResult(
                course_id=a.get("course_id"),
                assessment_id=a.get("assessment_id"),
                score=a.get("score"),
                passed=bool(a.get("passed")),
            )
            for a in raw.get("assessments", [])
            if a.get("course_id")
        )
        return LearnerProfile(
            user_id=user_id,
            enrolled_course_ids=frozenset(enrolled),
            progress=progress,
            assessments=assessments,
            certificate_course_ids=frozenset(raw.get("certificates", [])),
        )

    def execute(self, user_id: str) -> List[dict]:
        profile = self.build_profile(user_id)
        return self._engine.recommend(profile, self._catalog.list_snapshots())

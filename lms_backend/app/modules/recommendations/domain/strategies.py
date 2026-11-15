"""Reglas de recomendación como estrategias combinables (patrón Strategy).

Cada regla recibe el perfil del estudiante y los cursos CANDIDATOS (el motor
ya excluyó los inscritos y los propios) y devuelve sugerencias con su motivo.
El `RecommendationEngine` combina las reglas: si dos reglas sugieren el mismo
curso, gana la de mayor puntaje y se conservan los demás motivos.

Agregar una regla = crear una clase `RecommendationRule` y pasarla al motor
(OCP); no hay if/elif por tipo de regla. Dominio puro: sin dependencias.
"""

from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional, Sequence

from app.modules.recommendations.domain.models import (
    CourseSnapshot,
    LearnerProfile,
    Recommendation,
)


class RecommendationRule(ABC):
    """Estrategia: produce sugerencias para un perfil."""

    name: str = "rule"
    weight: float = 1.0

    @abstractmethod
    def recommend(
        self,
        profile: LearnerProfile,
        candidates: Sequence[CourseSnapshot],
        catalog: Dict[str, CourseSnapshot],
    ) -> List[Recommendation]:
        """`catalog` = todos los cursos por id (para leer los de referencia)."""

    def _make(self, course: CourseSnapshot, reason: str, bonus: float = 0.0) -> Recommendation:
        return Recommendation(
            course_id=course.course_id,
            title=course.title,
            reason=reason,
            rule=self.name,
            score=round(self.weight + bonus, 2),
        )


def _related(reference: CourseSnapshot, candidates: Iterable[CourseSnapshot]):
    """Candidatos del mismo instructor (primero) o del mismo tipo."""
    same_instructor = [
        c for c in candidates
        if reference.instructor_id and c.instructor_id == reference.instructor_id
    ]
    same_type = [
        c for c in candidates
        if c not in same_instructor and reference.course_type
        and c.course_type == reference.course_type
    ]
    return same_instructor, same_type


class ReinforceAfterFailedAssessmentRule(RecommendationRule):
    """Nota < aprobación -> cursos afines (mismo instructor o tipo) para reforzar."""

    name = "refuerzo"
    weight = 4.0

    def recommend(self, profile, candidates, catalog):
        out: List[Recommendation] = []
        for cid in profile.failed_course_ids():
            ref = catalog.get(cid)
            if ref is None:
                continue
            same_instructor, same_type = _related(ref, candidates)
            for c in same_instructor:
                out.append(self._make(c, (
                    f"Para reforzar: no aprobaste la evaluación de '{ref.title}' y "
                    f"este curso es del mismo instructor ({ref.instructor})."), 0.5))
            for c in same_type:
                out.append(self._make(c, (
                    f"Para reforzar: no aprobaste la evaluación de '{ref.title}' y "
                    f"este curso es del mismo tipo ({ref.course_type}).")))
        return out


class NextLevelAfterCertificateRule(RecommendationRule):
    """Curso certificado -> siguiente curso del mismo instructor/tipo."""

    name = "siguiente_nivel"
    weight = 3.5

    def recommend(self, profile, candidates, catalog):
        out: List[Recommendation] = []
        for cid in sorted(profile.certificate_course_ids):
            ref = catalog.get(cid)
            if ref is None:
                continue
            same_instructor, same_type = _related(ref, candidates)
            for c in same_instructor:
                out.append(self._make(c, (
                    f"Siguiente paso: obtuviste el certificado de '{ref.title}'; "
                    f"continúa con otro curso de {ref.instructor}."), 0.5))
            for c in same_type:
                out.append(self._make(c, (
                    f"Siguiente paso: obtuviste el certificado de '{ref.title}'; "
                    f"este curso es del mismo tipo ({ref.course_type}).")))
        return out


class SimilarToActiveCoursesRule(RecommendationRule):
    """Cursos con progreso (Visitor) -> afines por instructor o tipo."""

    name = "afinidad"
    weight = 2.5

    def recommend(self, profile, candidates, catalog):
        out: List[Recommendation] = []
        for cid in profile.active_course_ids():
            ref = catalog.get(cid)
            if ref is None:
                continue
            pct = profile.progress.get(cid, 0.0)
            same_instructor, same_type = _related(ref, candidates)
            bonus = pct / 100  # más avance -> más confianza
            for c in same_instructor:
                out.append(self._make(c, (
                    f"Llevas {pct:g}% de '{ref.title}'; este curso es del mismo "
                    f"instructor ({ref.instructor})."), 0.5 + bonus))
            for c in same_type:
                out.append(self._make(c, (
                    f"Llevas {pct:g}% de '{ref.title}'; este curso es del mismo "
                    f"tipo ({ref.course_type})."), bonus))
        return out


class PopularCoursesRule(RecommendationRule):
    """Los cursos con más inscripciones."""

    name = "popular"
    weight = 1.5

    def __init__(self, top: int = 3):
        self._top = top

    def recommend(self, profile, candidates, catalog):
        popular = sorted(
            (c for c in candidates if c.enrolled_count > 0),
            key=lambda c: (-c.enrolled_count, c.title),
        )[: self._top]
        return [
            self._make(c, (
                f"Popular: {c.enrolled_count} estudiante(s) inscrito(s)."),
                min(c.enrolled_count, 10) / 10)
            for c in popular
        ]


class FreeCoursesForNewcomersRule(RecommendationRule):
    """Estudiante sin inscripciones -> cursos gratuitos para empezar."""

    name = "gratis_para_empezar"
    weight = 2.0

    def recommend(self, profile, candidates, catalog):
        if not profile.is_newcomer:
            return []
        return [
            self._make(c, "Gratis para empezar: aún no tienes cursos y este no requiere pago.")
            for c in candidates if c.is_free
        ]


def default_rules() -> List[RecommendationRule]:
    return [
        ReinforceAfterFailedAssessmentRule(),
        NextLevelAfterCertificateRule(),
        SimilarToActiveCoursesRule(),
        FreeCoursesForNewcomersRule(),
        PopularCoursesRule(),
    ]


class RecommendationEngine:
    """Combina estrategias. Excluye cursos inscritos y propios del usuario."""

    def __init__(self, rules: Optional[Sequence[RecommendationRule]] = None, limit: int = 10):
        self._rules = list(rules) if rules is not None else default_rules()
        self._limit = limit

    def recommend(
        self, profile: LearnerProfile, courses: Sequence[CourseSnapshot]
    ) -> List[dict]:
        catalog = {c.course_id: c for c in courses}
        candidates = [
            c for c in courses
            if c.course_id not in profile.enrolled_course_ids
            and c.instructor_id != profile.user_id
        ]

        best: Dict[str, Recommendation] = {}
        reasons: Dict[str, List[str]] = {}
        for rule in self._rules:
            for rec in rule.recommend(profile, candidates, catalog):
                reasons.setdefault(rec.course_id, [])
                if rec.reason not in reasons[rec.course_id]:
                    reasons[rec.course_id].append(rec.reason)
                current = best.get(rec.course_id)
                if current is None or rec.score > current.score:
                    best[rec.course_id] = rec

        ranked = sorted(best.values(), key=lambda r: (-r.score, r.title))[: self._limit]
        result = []
        for rec in ranked:
            course = catalog[rec.course_id]
            result.append({
                **rec.to_dict(),
                "reasons": reasons[rec.course_id],
                "instructor": course.instructor,
                "type": course.course_type,
                "price": course.price,
                "premium": course.premium,
                "certificate": course.has_certificate,
            })
        return result

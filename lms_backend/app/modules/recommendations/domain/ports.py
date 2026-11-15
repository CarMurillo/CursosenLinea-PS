"""Puerto del perfil de aprendizaje (lo alimenta RecommendationProfileObserver).

La fase backend-objetivos lo usa para generar recomendaciones por reglas.
"""

from typing import Any, Mapping, Optional, Protocol


class LearningProfilePort(Protocol):
    def record_enrollment(self, user_id: str, course_id: str) -> None: ...

    def record_lesson_completed(
        self, user_id: str, course_id: str, lesson_id: Optional[str]
    ) -> None: ...

    def record_assessment(
        self, user_id: str, course_id: str, details: Mapping[str, Any]
    ) -> None: ...

    def record_certificate(self, user_id: str, course_id: str) -> None: ...

    def get_profile(self, user_id: str) -> dict: ...

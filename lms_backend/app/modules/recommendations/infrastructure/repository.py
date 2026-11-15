"""Perfil de aprendizaje en memoria (cumple LearningProfilePort).

Provisional: la fase backend-objetivos lo consume para las recomendaciones.
"""

import threading
from typing import Any, Dict, Mapping, Optional


def _empty_profile() -> dict:
    return {
        "enrolled_courses": [],
        "completed_lessons": {},   # course_id -> [lesson_id]
        "assessments": [],         # [{course_id, assessment_id, score, passed}]
        "certificates": [],        # [course_id]
    }


class InMemoryLearningProfileRepository:
    def __init__(self):
        self._profiles: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def _profile(self, user_id: str) -> dict:
        return self._profiles.setdefault(user_id, _empty_profile())

    def record_enrollment(self, user_id: str, course_id: str) -> None:
        with self._lock:
            courses = self._profile(user_id)["enrolled_courses"]
            if course_id not in courses:
                courses.append(course_id)

    def record_lesson_completed(
        self, user_id: str, course_id: str, lesson_id: Optional[str]
    ) -> None:
        with self._lock:
            lessons = self._profile(user_id)["completed_lessons"].setdefault(course_id, [])
            if lesson_id and lesson_id not in lessons:
                lessons.append(lesson_id)

    def record_assessment(
        self, user_id: str, course_id: str, details: Mapping[str, Any]
    ) -> None:
        with self._lock:
            self._profile(user_id)["assessments"].append({
                "course_id": course_id,
                "assessment_id": details.get("assessment_id"),
                "score": details.get("score"),
                "passed": bool(details.get("passed")),
            })

    def record_certificate(self, user_id: str, course_id: str) -> None:
        with self._lock:
            certs = self._profile(user_id)["certificates"]
            if course_id not in certs:
                certs.append(course_id)

    def get_profile(self, user_id: str) -> dict:
        with self._lock:
            profile = self._profiles.get(user_id) or _empty_profile()
            # copia para que el llamador no mute el estado interno
            return {
                "enrolled_courses": list(profile["enrolled_courses"]),
                "completed_lessons": {k: list(v) for k, v in profile["completed_lessons"].items()},
                "assessments": [dict(a) for a in profile["assessments"]],
                "certificates": list(profile["certificates"]),
            }

    def clear(self) -> None:
        with self._lock:
            self._profiles.clear()

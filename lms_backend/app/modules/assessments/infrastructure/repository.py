import threading
from typing import Dict, List, Optional

from app.modules.assessments.domain.models import Assessment


class InMemoryAssessmentRepository:
    def __init__(self):
        self._items: Dict[str, Assessment] = {}
        self._lock = threading.Lock()

    def save(self, assessment: Assessment) -> Assessment:
        with self._lock:
            self._items[assessment.assessment_id] = assessment
        return assessment

    def get_by_id(self, assessment_id: str) -> Optional[Assessment]:
        return self._items.get(assessment_id)

    def list_by_course(self, course_id: str) -> List[Assessment]:
        return [a for a in self._items.values() if a.course_id == course_id]

    def count(self) -> int:
        with self._lock:
            return len(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

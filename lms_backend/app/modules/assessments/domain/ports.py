from typing import List, Optional, Protocol

from app.modules.assessments.domain.models import Assessment


class AssessmentRepository(Protocol):
    def save(self, assessment: Assessment) -> Assessment: ...

    def get_by_id(self, assessment_id: str) -> Optional[Assessment]: ...

    def list_by_course(self, course_id: str) -> List[Assessment]: ...

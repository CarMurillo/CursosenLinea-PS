"""Endpoints de evaluaciones (patrón State).

`router`         -> /assessments*
`courses_router` -> GET /courses/{course_id}/assessments
"""

from fastapi import APIRouter, Depends

from app.modules.assessments.application.dtos import (
    AssessmentCreateDTO,
    AttemptSubmitDTO,
    QuestionCreateDTO,
)
from app.modules.assessments.application.use_cases import AssessmentService
from app.modules.assessments.domain.models import AttemptLimitReached
from app.shared.infrastructure import container
from app.shared.infrastructure.auth_deps import get_current_user, require_role
from app.shared.infrastructure.http_errors import domain_errors_as_http

router = APIRouter(prefix="/assessments", tags=["assessments"])
courses_router = APIRouter(prefix="/courses", tags=["assessments"])

require_staff = require_role("instructor", "admin")
require_student = require_role("student")

_ERRORS = {AttemptLimitReached: 409}


def get_assessment_service() -> AssessmentService:
    return container.make_assessment_service()


@router.post("", status_code=201)
def create_assessment(
    dto: AssessmentCreateDTO,
    user=Depends(require_staff),
    service: AssessmentService = Depends(get_assessment_service),
):
    with domain_errors_as_http(_ERRORS):
        assessment = service.create(
            course_id=dto.course_id,
            title=dto.title,
            description=dto.description,
            passing_score=dto.passing_score,
            max_attempts=dto.max_attempts,
            user_id=user.id,
            role=user.role,
        )
    return assessment.to_dict()


@router.post("/{assessment_id}/questions", status_code=201)
def add_question(
    assessment_id: str,
    dto: QuestionCreateDTO,
    user=Depends(require_staff),
    service: AssessmentService = Depends(get_assessment_service),
):
    with domain_errors_as_http(_ERRORS):
        question = service.add_question(
            assessment_id,
            user_id=user.id,
            role=user.role,
            text=dto.text,
            options=dto.options,
            correct_option=dto.correct_option,
            points=dto.points,
        )
    return question.to_dict(include_answer=True)


@router.post("/{assessment_id}/publish")
def publish_assessment(
    assessment_id: str,
    user=Depends(require_staff),
    service: AssessmentService = Depends(get_assessment_service),
):
    with domain_errors_as_http(_ERRORS):
        return service.publish(assessment_id, user_id=user.id, role=user.role).to_dict()


@router.post("/{assessment_id}/close")
def close_assessment(
    assessment_id: str,
    user=Depends(require_staff),
    service: AssessmentService = Depends(get_assessment_service),
):
    with domain_errors_as_http(_ERRORS):
        return service.close(assessment_id, user_id=user.id, role=user.role).to_dict()


@router.post("/{assessment_id}/attempts", status_code=201)
def submit_attempt(
    assessment_id: str,
    dto: AttemptSubmitDTO,
    user=Depends(require_student),
    service: AssessmentService = Depends(get_assessment_service),
):
    with domain_errors_as_http(_ERRORS):
        attempt = service.submit_attempt(
            assessment_id, user_id=user.id, answers=dto.answers
        )
    return attempt.to_dict()


@router.get("/{assessment_id}")
def get_assessment(
    assessment_id: str,
    user=Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service),
):
    with domain_errors_as_http(_ERRORS):
        return service.get_for_user(assessment_id, user_id=user.id, role=user.role)


@courses_router.get("/{course_id}/assessments")
def list_course_assessments(
    course_id: str,
    user=Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service),
):
    with domain_errors_as_http(_ERRORS):
        return service.list_for_course(course_id, user_id=user.id, role=user.role)

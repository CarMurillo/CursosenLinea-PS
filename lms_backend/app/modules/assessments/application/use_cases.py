"""
Casos de uso de evaluaciones.

Reglas de autorización (además del rol que exige la API):
- Crear, agregar preguntas, publicar y cerrar: instructor dueño del curso o admin.
- Rendir: estudiante inscrito en el curso.
- Consultar: dueño/admin ven todo (incluidas respuestas correctas e intentos);
  estudiantes inscritos ven solo evaluaciones visibles (no borradores) y sin
  respuestas correctas.

Ninguna regla de ciclo de vida vive aquí: se delegan en el estado de la
evaluación (patrón State). Al calificar se publican ASSESSMENT_SUBMITTED y
ASSESSMENT_GRADED en el bus de eventos (Observer).
"""

from __future__ import annotations

from typing import List, Mapping, Optional

from app.modules.assessments.domain.models import Assessment, Attempt, Question
from app.modules.assessments.domain.ports import AssessmentRepository
from app.shared.domain.errors import PermissionDenied, ResourceNotFound
from app.shared.domain.events import (
    DomainEvent,
    EventPublisher,
    EventType,
    publish_event,
)
from app.shared.domain.state import CourseCatalogPort, CourseInfo


class AssessmentService:
    def __init__(
        self,
        repository: AssessmentRepository,
        courses: CourseCatalogPort,
        event_bus: Optional[EventPublisher] = None,
    ):
        self._repository = repository
        self._courses = courses
        self._event_bus = event_bus

    # ------------------------------------------------------------ utilidades
    def _course(self, course_id: str) -> CourseInfo:
        course = self._courses.get_course_info(course_id)
        if course is None:
            raise ResourceNotFound("Curso no encontrado")
        return course

    def _assessment(self, assessment_id: str) -> Assessment:
        assessment = self._repository.get_by_id(assessment_id)
        if assessment is None:
            raise ResourceNotFound("Evaluación no encontrada")
        return assessment

    def _managed(self, assessment_id: str, user_id: str, role: str) -> Assessment:
        assessment = self._assessment(assessment_id)
        if not self._course(assessment.course_id).is_managed_by(user_id, role):
            raise PermissionDenied(
                "Solo el instructor dueño del curso puede gestionar la evaluación."
            )
        return assessment

    # ------------------------------------------------------- instructor/admin
    def create(
        self,
        *,
        course_id: str,
        title: str,
        user_id: str,
        role: str,
        passing_score: float = 60.0,
        max_attempts: int = 1,
        description: str = "",
    ) -> Assessment:
        if not self._course(course_id).is_managed_by(user_id, role):
            raise PermissionDenied(
                "Solo el instructor dueño del curso puede crear evaluaciones."
            )
        assessment = Assessment(
            course_id,
            title,
            created_by=user_id,
            passing_score=passing_score,
            max_attempts=max_attempts,
            description=description,
        )
        return self._repository.save(assessment)

    def add_question(
        self,
        assessment_id: str,
        *,
        user_id: str,
        role: str,
        text: str,
        options: List[str],
        correct_option: int,
        points: float = 1.0,
    ) -> Question:
        assessment = self._managed(assessment_id, user_id, role)
        question = Question(text, list(options), correct_option, points)
        assessment.add_question(question)          # delega en el estado
        self._repository.save(assessment)
        return question

    def publish(self, assessment_id: str, *, user_id: str, role: str) -> Assessment:
        assessment = self._managed(assessment_id, user_id, role)
        assessment.publish()                       # delega en el estado
        return self._repository.save(assessment)

    def close(self, assessment_id: str, *, user_id: str, role: str) -> Assessment:
        assessment = self._managed(assessment_id, user_id, role)
        assessment.close()                         # delega en el estado
        return self._repository.save(assessment)

    # ------------------------------------------------------------ estudiante
    def submit_attempt(
        self, assessment_id: str, *, user_id: str, answers: Mapping[str, int]
    ) -> Attempt:
        assessment = self._assessment(assessment_id)
        course = self._course(assessment.course_id)
        if not course.is_enrolled(user_id):
            raise PermissionDenied(
                "Debes estar inscrito en el curso para rendir la evaluación."
            )
        attempt = assessment.submit_attempt(user_id, answers)  # delega en el estado
        self._repository.save(assessment)

        publish_event(self._event_bus, DomainEvent(
            EventType.ASSESSMENT_SUBMITTED,
            user_id=user_id,
            course_id=course.course_id,
            payload={
                "assessment_id": assessment.assessment_id,
                "attempt_id": attempt.attempt_id,
            },
        ))
        publish_event(self._event_bus, DomainEvent(
            EventType.ASSESSMENT_GRADED,
            user_id=user_id,
            course_id=course.course_id,
            payload={
                "assessment_id": assessment.assessment_id,
                "attempt_id": attempt.attempt_id,
                "assessment_title": assessment.title,
                "score": attempt.score,
                "max_score": attempt.max_score,
                "percentage": attempt.percentage,
                "passing_score": assessment.passing_score,
                "passed": attempt.passed,
                "course_title": course.title,
            },
        ))
        return attempt

    # -------------------------------------------------------------- consultas
    def get_for_user(self, assessment_id: str, *, user_id: str, role: str) -> dict:
        assessment = self._assessment(assessment_id)
        course = self._course(assessment.course_id)
        if course.is_managed_by(user_id, role):
            data = assessment.to_dict(include_answers=True)
            data["attempts"] = [a.to_dict() for a in assessment.attempts]
            return data
        if not course.is_enrolled(user_id):
            raise PermissionDenied("No tienes acceso a las evaluaciones de este curso.")
        if not assessment.visible_to_students:
            # Los borradores no existen para el estudiante.
            raise ResourceNotFound("Evaluación no encontrada")
        data = assessment.to_dict(include_answers=False)
        data["my_attempts"] = [a.to_dict() for a in assessment.attempts_of(user_id)]
        return data

    def list_for_course(self, course_id: str, *, user_id: str, role: str) -> List[dict]:
        course = self._course(course_id)
        assessments = self._repository.list_by_course(course_id)
        if course.is_managed_by(user_id, role):
            return [a.to_dict(include_answers=True) for a in assessments]
        if not course.is_enrolled(user_id):
            raise PermissionDenied("No tienes acceso a las evaluaciones de este curso.")
        return [
            a.to_dict(include_answers=False)
            for a in assessments
            if a.visible_to_students
        ]

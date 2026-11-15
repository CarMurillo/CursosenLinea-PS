"""
Patrón State (GoF): estados del ciclo de vida de una evaluación.

    DraftState --publish--> PublishedState --close--> ClosedState

El contexto (`Assessment`) delega TODA operación dependiente del estado en
su objeto `AssessmentState`. Cada estado concreto decide si la operación es
válida (la ejecuta y, si procede, cambia el estado del contexto) o lanza
`InvalidStateTransition`. No hay `if state == ...` en el contexto ni en los
casos de uso: agregar un estado nuevo (p. ej. `ArchivedState`) solo requiere
una clase nueva que implemente esta interfaz y una transición que lo active.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Mapping

from app.shared.domain.state import InvalidStateTransition

if TYPE_CHECKING:  # pragma: no cover
    from app.modules.assessments.domain.models import Assessment, Attempt, Question


class AssessmentState(ABC):
    """Interfaz común de los estados de una evaluación."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre estable del estado (se expone en la API)."""

    @property
    @abstractmethod
    def visible_to_students(self) -> bool:
        """Si los estudiantes inscritos pueden ver la evaluación."""

    @abstractmethod
    def add_question(self, assessment: "Assessment", question: "Question") -> None: ...

    @abstractmethod
    def publish(self, assessment: "Assessment") -> None: ...

    @abstractmethod
    def submit_attempt(
        self, assessment: "Assessment", user_id: str, answers: Mapping[str, int]
    ) -> "Attempt": ...

    @abstractmethod
    def close(self, assessment: "Assessment") -> None: ...

    # ----------------------------------------------------------- utilidades
    def _reject(self, action: str, detail: str = "") -> InvalidStateTransition:
        return InvalidStateTransition("la evaluación", self.name, action, detail)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{type(self).__name__}>"


class DraftState(AssessmentState):
    """Borrador: se editan preguntas; aún no admite intentos."""

    name = "draft"
    visible_to_students = False

    def add_question(self, assessment, question):
        assessment._append_question(question)

    def publish(self, assessment):
        if not assessment.questions:
            raise self._reject(
                "publicar", "Agrega al menos una pregunta antes de publicar."
            )
        assessment._transition_to(PublishedState())

    def submit_attempt(self, assessment, user_id, answers):
        raise self._reject("rendir", "La evaluación aún no está publicada.")

    def close(self, assessment):
        raise self._reject("cerrar", "Solo se cierra una evaluación publicada.")


class PublishedState(AssessmentState):
    """Publicada: admite intentos con calificación automática."""

    name = "published"
    visible_to_students = True

    def add_question(self, assessment, question):
        raise self._reject(
            "agregar preguntas a", "Solo se editan evaluaciones en borrador."
        )

    def publish(self, assessment):
        raise self._reject("publicar", "La evaluación ya está publicada.")

    def submit_attempt(self, assessment, user_id, answers):
        return assessment._grade_and_record(user_id, answers)

    def close(self, assessment):
        assessment._transition_to(ClosedState())


class ClosedState(AssessmentState):
    """Cerrada: sin edición ni intentos; los resultados siguen consultables."""

    name = "closed"
    visible_to_students = True

    def add_question(self, assessment, question):
        raise self._reject("agregar preguntas a", "La evaluación está cerrada.")

    def publish(self, assessment):
        raise self._reject("publicar", "La evaluación está cerrada.")

    def submit_attempt(self, assessment, user_id, answers):
        raise self._reject("rendir", "La evaluación está cerrada.")

    def close(self, assessment):
        raise self._reject("cerrar", "La evaluación ya está cerrada.")


# Alias en español (nomenclatura usada en el plan del proyecto).
BorradorState = DraftState
PublicadaState = PublishedState
CerradaState = ClosedState

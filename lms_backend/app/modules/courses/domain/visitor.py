"""
Módulo: Courses - Capa de Dominio
Patrón de Diseño: Visitor (Comportamiento) sobre el árbol Composite.

Cada componente del contenido (CourseContent, LessonModule, VideoLesson,
InteractiveQuizLesson y ProtectedContentProxy) implementa `accept(visitor)`.
Las operaciones sobre el árbol viven aquí, en visitantes concretos, de modo
que:

- agregar una operación nueva = agregar un visitante (OCP), sin tocar las
  clases del Composite;
- el cliente nunca usa `isinstance` para saber qué nodo está recorriendo:
  el doble despacho (`accept` -> `visit_*`) lo resuelve.

Relación con Flyweight: los metadatos de tipo de lección son estado
intrínseco compartido (ContentMetadataFactory). El progreso de cada
estudiante (lecciones completadas) es estado EXTRÍNSECO: no se guarda en las
lecciones sino en ProgressRepository y se pasa al ProgressVisitor.
"""

from abc import ABC, abstractmethod
from typing import Iterable

from app.modules.courses.domain.bridge import (
    InteractiveQuizLesson,
    LessonContent,
    VideoLesson,
)
from app.modules.courses.domain.composite import CourseContent, LessonModule


# ============================================================
# INTERFAZ DEL VISITANTE
# ============================================================

class ContentVisitor(ABC):
    """
    Visitante del árbol de contenido.

    - visit_module / visit_lesson son obligatorios.
    - visit_video_lesson / visit_quiz_lesson delegan por defecto en
      visit_lesson; un visitante los sobrescribe si necesita distinguir el
      tipo de lección.
    - visit_course / leave_course / leave_module son ganchos opcionales
      (raíz del curso y salida de un módulo, útil para anidar el temario).
    """

    @abstractmethod
    def visit_module(self, module: LessonModule) -> None:
        pass

    @abstractmethod
    def visit_lesson(self, lesson: LessonContent) -> None:
        pass

    def visit_video_lesson(self, lesson: VideoLesson) -> None:
        self.visit_lesson(lesson)

    def visit_quiz_lesson(self, lesson: InteractiveQuizLesson) -> None:
        self.visit_lesson(lesson)

    def visit_course(self, content: CourseContent) -> None:
        """Gancho: inicio del recorrido en la raíz del curso."""

    def leave_course(self, content: CourseContent) -> None:
        """Gancho: fin del recorrido en la raíz del curso."""

    def leave_module(self, module: LessonModule) -> None:
        """Gancho: se terminaron de visitar los hijos del módulo."""


# ============================================================
# VISITANTES CONCRETOS
# ============================================================

class DurationVisitor(ContentVisitor):
    """Duración total del contenido en minutos."""

    def __init__(self):
        self.total_minutes = 0

    def visit_module(self, module: LessonModule) -> None:
        pass

    def visit_lesson(self, lesson: LessonContent) -> None:
        self.total_minutes += lesson.duration_minutes


class LessonIndexVisitor(ContentVisitor):
    """Recolecta los lesson_id del árbol (para validar que una lección existe)."""

    def __init__(self):
        self.lesson_ids: set[str] = set()

    def visit_module(self, module: LessonModule) -> None:
        pass

    def visit_lesson(self, lesson: LessonContent) -> None:
        self.lesson_ids.add(lesson.lesson_id)

    def contains(self, lesson_id: str) -> bool:
        return lesson_id in self.lesson_ids


class ProgressVisitor(ContentVisitor):
    """
    Progreso de un estudiante.

    Recibe el estado extrínseco (ids de lecciones completadas) y calcula
    lecciones completadas / total, porcentaje y minutos. Ignora ids que ya
    no existan en el árbol (lecciones eliminadas).
    """

    def __init__(self, completed_lesson_ids: Iterable[str]):
        self._completed = set(completed_lesson_ids)
        self.total_lessons = 0
        self.completed_lessons = 0
        self.total_minutes = 0
        self.completed_minutes = 0
        self.completed_lesson_ids: list[str] = []

    def visit_module(self, module: LessonModule) -> None:
        pass

    def visit_lesson(self, lesson: LessonContent) -> None:
        self.total_lessons += 1
        self.total_minutes += lesson.duration_minutes
        if lesson.lesson_id in self._completed:
            self.completed_lessons += 1
            self.completed_minutes += lesson.duration_minutes
            self.completed_lesson_ids.append(lesson.lesson_id)

    @property
    def percentage(self) -> float:
        if self.total_lessons == 0:
            return 0.0
        return round(self.completed_lessons * 100 / self.total_lessons, 2)

    def result(self) -> dict:
        return {
            "completed_lessons": self.completed_lessons,
            "total_lessons": self.total_lessons,
            "percentage": self.percentage,
            "completed_minutes": self.completed_minutes,
            "total_minutes": self.total_minutes,
            "completed_lesson_ids": list(self.completed_lesson_ids),
        }


class ContentSummaryVisitor(ContentVisitor):
    """
    Resumen del temario: número de módulos y lecciones, conteo por tipo,
    duración total y árbol de módulos con sus lecciones.
    """

    def __init__(self):
        self.title: str | None = None
        self.module_count = 0
        self.lesson_count = 0
        self.total_minutes = 0
        self.by_type: dict[str, int] = {}
        # Nodo raíz del temario; la pila sigue el módulo actual.
        self._root = {"title": None, "lessons": [], "modules": []}
        self._stack: list[dict] = [self._root]

    def visit_course(self, content: CourseContent) -> None:
        self.title = content.title
        self._root["title"] = content.title

    def visit_module(self, module: LessonModule) -> None:
        self.module_count += 1
        node = {
            "title": module.title,
            "lessons": [],
            "modules": [],
            "duration_minutes": 0,
        }
        self._stack[-1]["modules"].append(node)
        self._stack.append(node)

    def leave_module(self, module: LessonModule) -> None:
        node = self._stack.pop()
        # La duración del módulo padre incluye la de sus submódulos.
        parent = self._stack[-1]
        if "duration_minutes" in parent:
            parent["duration_minutes"] += node["duration_minutes"]

    def visit_lesson(self, lesson: LessonContent) -> None:
        content_type = lesson.metadata.content_type
        self.lesson_count += 1
        self.total_minutes += lesson.duration_minutes
        self.by_type[content_type] = self.by_type.get(content_type, 0) + 1
        current = self._stack[-1]
        current["lessons"].append({
            "lesson_id": lesson.lesson_id,
            "title": lesson.title,
            "type": content_type,
            "label": lesson.metadata.label,
            "duration_minutes": lesson.duration_minutes,
        })
        if "duration_minutes" in current:
            current["duration_minutes"] += lesson.duration_minutes

    def result(self) -> dict:
        return {
            "title": self.title,
            "total_modules": self.module_count,
            "total_lessons": self.lesson_count,
            "total_minutes": self.total_minutes,
            "lessons_by_type": dict(self.by_type),
            "syllabus": self._root["modules"],
            # Lecciones colgadas directamente de la raíz (sin módulo).
            "loose_lessons": self._root["lessons"],
        }


class ExportSyllabusVisitor(ContentVisitor):
    """Exporta el temario como texto Markdown."""

    def __init__(self):
        self._lines: list[str] = []
        self._depth = 0

    def visit_course(self, content: CourseContent) -> None:
        self._lines.append(f"# {content.title}")

    def visit_module(self, module: LessonModule) -> None:
        self._depth += 1
        self._lines.append(f"{'#' * (self._depth + 1)} {module.title}")

    def leave_module(self, module: LessonModule) -> None:
        self._depth -= 1

    def visit_lesson(self, lesson: LessonContent) -> None:
        self._lines.append(
            f"- [{lesson.metadata.label}] {lesson.title} "
            f"({lesson.duration_minutes} min)"
        )

    def to_markdown(self) -> str:
        return "\n".join(self._lines)

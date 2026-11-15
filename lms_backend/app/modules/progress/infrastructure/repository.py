from app.modules.progress.domain.ports import ProgressRepository


class InMemoryProgressRepository(ProgressRepository):
    """Adaptador en memoria del puerto ProgressRepository."""

    def __init__(self):
        self._completed: dict[tuple[str, str], set[str]] = {}

    def mark_completed(self, user_id: str, course_id: str, lesson_id: str) -> bool:
        lessons = self._completed.setdefault((user_id, course_id), set())
        if lesson_id in lessons:
            return False
        lessons.add(lesson_id)
        return True

    def completed_lessons(self, user_id: str, course_id: str) -> set[str]:
        return set(self._completed.get((user_id, course_id), set()))

    def clear(self) -> None:
        self._completed.clear()



# La instancia compartida la crea el composition root:
# app/shared/infrastructure/container.py (`container.progress_repository`).


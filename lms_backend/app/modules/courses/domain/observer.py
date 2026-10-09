
from abc import ABC, abstractmethod
from typing import List


class Observer(ABC):
    @abstractmethod
    def update(self, student_name: str, course_title: str) -> None:
        pass


class Subject:
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def notify(self, student_name: str, course_title: str) -> None:
        for observer in self._observers:
            observer.update(student_name, course_title)


# --- Observers Concretos ---
class EmailNotificationObserver(Observer):
    def update(self, student_name: str, course_title: str) -> None:
        print(f"  Enviando correo a {student_name}: Inscripción confirmada a '{course_title}'.")


class LoggingObserver(Observer):
    def update(self, student_name: str, course_title: str) -> None:
        print(f"  [AUDITORÍA] El estudiante {student_name} se matriculó en '{course_title}'.")

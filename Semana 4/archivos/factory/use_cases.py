"""Casos de uso del módulo de cursos.

Conecta el Factory Method (CourseFactory) para publicar módulos y el
Observer (Subject + observadores concretos) para notificar
matrículas, ambos ya definidos en el dominio.
"""

import uuid

from app.modules.courses.application.dtos import CourseCreateDTO
from app.modules.courses.domain.models import Course, CourseFactory
from app.modules.courses.domain.observer import (
    EmailNotificationObserver,
    LoggingObserver,
    Subject,
)
from app.modules.courses.domain.ports import CourseRepository


class CourseNotFoundError(Exception):
    pass


class PublishCourseUseCase:
    """Usado por instructores para publicar un nuevo módulo/curso."""

    def __init__(self, repository: CourseRepository):
        self.repository = repository

    def execute(self, dto: CourseCreateDTO) -> Course:
        # --- PATRÓN GOF: FACTORY METHOD ---
        # CourseFactory decide qué subclase de Course instanciar
        # (VideoCourse o LiveClassCourse) según course_type, sin acoplar
        # este caso de uso a las clases concretas.
        course = CourseFactory.create_course(
            course_type=dto.course_type,
            course_id=str(uuid.uuid4()),
            title=dto.title,
            instructor=dto.instructor,
            price=dto.price,
        )
        return self.repository.save(course)


class EnrollStudentUseCase:
    """Usado por estudiantes para matricularse en un curso."""

    def __init__(self, repository: CourseRepository):
        self.repository = repository
        # --- PATRÓN GOF: OBSERVER ---
        # Cada matrícula dispara notificaciones desacopladas del caso de uso.
        self._notifier = Subject()
        self._notifier.attach(EmailNotificationObserver())
        self._notifier.attach(LoggingObserver())

    def execute(self, course_id: str, student_name: str) -> Course:
        course = self.repository.get_by_id(course_id)
        if not course:
            raise CourseNotFoundError(course_id)

        course.enrolled_students.append(student_name)
        self._notifier.notify(student_name, course.title)
        return course


class ListCoursesUseCase:
    def __init__(self, repository: CourseRepository):
        self.repository = repository

    def execute(self) -> list[Course]:
        return self.repository.list_all()
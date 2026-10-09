
from app.modules.auth.domain.models import Role, Student, Instructor
from app.modules.auth.domain.factories import UserCreationService


def test_create_student():
    student = UserCreationService.register_user(
        role=Role.STUDENT,
        first_name="Carlos",
        last_name="Murillo",
        email="carlos@example.com",
        password_hash="hashed_secret"
    )

    assert isinstance(student, Student)
    assert student.role == Role.STUDENT
    assert student.full_name == "Carlos Murillo"
    assert student.enrolled_courses == []


def test_create_instructor():
    instructor = UserCreationService.register_user(
        role=Role.INSTRUCTOR,
        first_name="Eliecer",
        last_name="Montero",
        email="montero@example.com",
        password_hash="hashed_secret",
        specialization="Arquitectura de Software"
    )

    assert isinstance(instructor, Instructor)
    assert instructor.role == Role.INSTRUCTOR
    assert instructor.specialization == "Arquitectura de Software"


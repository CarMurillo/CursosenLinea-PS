from app.modules.courses.domain.builder import CourseBuilder
from app.modules.courses.domain.models import (
    VideoCourse,
    LiveClassCourse,
)
from app.modules.courses.infrastructure.repository import (
    InMemoryCourseRepository,
)


# ============================================================
# TEST BUILDER
# ============================================================

def test_builder_creates_video_course():

    course = (
        CourseBuilder()
        .set_title("Python desde cero")
        .set_instructor("Carlos Murillo")
        .set_price(50)
        .set_course_type("video")
        .build()
    )

    assert isinstance(course, VideoCourse)

    assert course.title == "Python desde cero"

    assert course.instructor == "Carlos Murillo"

    assert course.price == 50


def test_builder_creates_live_course():

    course = (
        CourseBuilder()
        .set_title("Programación en vivo")
        .set_instructor("Carlos Murillo")
        .set_price(80)
        .set_course_type("live")
        .build()
    )

    assert isinstance(course, LiveClassCourse)

    assert course.title == "Programación en vivo"

    assert course.price == 80


def test_builder_rejects_negative_price():

    try:

        (
            CourseBuilder()
            .set_title("Curso de prueba")
            .set_instructor("Carlos")
            .set_price(-10)
            .build()
        )

        assert False

    except ValueError:

        assert True


# ============================================================
# TEST PROTOTYPE
# ============================================================

def test_prototype_clones_course():

    original = (
        CourseBuilder()
        .set_title("Python desde cero")
        .set_instructor("Carlos Murillo")
        .set_price(50)
        .set_course_type("video")
        .build()
    )

    original.enrolled_students.append(
        "Estudiante Original"
    )

    cloned = original.clone()

    # Deben ser objetos diferentes
    assert cloned is not original

    # Deben tener IDs diferentes
    assert cloned.course_id != original.course_id

    # Los datos principales se conservan
    assert cloned.title == original.title

    assert cloned.instructor == original.instructor

    assert cloned.price == original.price

    # El clon empieza sin estudiantes
    assert cloned.enrolled_students == []

    # El original conserva sus estudiantes
    assert original.enrolled_students == [
        "Estudiante Original"
    ]


# ============================================================
# TEST REPOSITORY + PROTOTYPE
# ============================================================

def test_clone_is_saved_in_repository():

    repository = InMemoryCourseRepository()

    original = (
        CourseBuilder()
        .set_title("Curso original")
        .set_instructor("Carlos")
        .set_price(30)
        .set_course_type("video")
        .build()
    )

    repository.save(original)

    cloned = original.clone()

    cloned.title = "Curso original - Grupo 2"

    repository.save(cloned)

    courses = repository.list_all()

    assert len(courses) == 2

    assert courses[0].course_id != courses[1].course_id

    assert courses[1].title == (
        "Curso original - Grupo 2"
    )   
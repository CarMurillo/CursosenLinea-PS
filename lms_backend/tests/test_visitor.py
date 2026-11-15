"""Pruebas del patrón Visitor sobre el Composite (duración, progreso, temario)
y de los endpoints de progreso/resumen protegidos por el Proxy."""

import pytest

from app.modules.courses.domain.bridge import (
    InteractiveQuizLesson,
    S3StorageProvider,
    VideoLesson,
    VimeoStorageProvider,
)
from app.modules.courses.domain.composite import CourseContent, LessonModule
from app.modules.courses.domain.content_proxy import (
    ContentAccessDenied,
    EnrolledStudentPolicy,
    ProtectedContentProxy,
)
from app.modules.courses.domain.models import VideoCourse
from app.modules.courses.domain.visitor import (
    ContentSummaryVisitor,
    ContentVisitor,
    DurationVisitor,
    ExportSyllabusVisitor,
    LessonIndexVisitor,
    ProgressVisitor,
)
from app.modules.courses.infrastructure.repository import course_repository
from app.modules.progress.application.use_cases import (
    CompleteLessonUseCase,
    LessonNotFoundError,
)
from app.modules.progress.infrastructure.repository import (
    InMemoryProgressRepository,
    progress_repository,
)

PWD = "Secreta123"


@pytest.fixture(autouse=True)
def _reset_progress_repository():
    progress_repository.clear()
    yield
    progress_repository.clear()


# ------------------------------------------------------------------ helpers

def _tree():
    """Curso con 2 módulos: 2 videos (10 + 20) y 1 quiz (15) = 45 min."""
    content = CourseContent("Python")
    v1 = VideoLesson("Intro", "m1", VimeoStorageProvider(), duration_minutes=10)
    v2 = VideoLesson("Tipos", "m2", S3StorageProvider(), duration_minutes=20)
    q1 = InteractiveQuizLesson("Quiz 1", "q1", VimeoStorageProvider(), duration_minutes=15)
    content.add_lesson("Fundamentos", v1)
    content.add_lesson("Fundamentos", v2)
    content.add_lesson("Evaluación", q1)
    return content, v1, v2, q1


def _login(client, email, role):
    client.post("/auth/register", json={"first_name": "Ana", "last_name": "Perez",
        "email": email, "password": PWD, "role": role})
    r = client.post("/auth/login", json={"email": email, "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _course(client, headers, **overrides):
    body = {"title": "Py", "price": 0, "course_type": "video"}
    body.update(overrides)
    r = client.post("/courses/", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _lesson(client, headers, cid, module="M1", lesson_type="video", minutes=None):
    body = {"module_title": module, "title": "L", "media_id": "x",
            "provider": "vimeo", "lesson_type": lesson_type}
    if minutes is not None:
        body["duration_minutes"] = minutes
    r = client.post(f"/courses/{cid}/content/lessons", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["lesson_id"]


def _paid_course_with_lessons(client):
    inst = _login(client, "i@x.com", "instructor")
    cid = _course(client, inst, price=50)
    l1 = _lesson(client, inst, cid, minutes=30)
    l2 = _lesson(client, inst, cid, module="M2", lesson_type="quiz", minutes=10)
    return inst, cid, l1, l2


def _enroll_paid(client, headers, cid):
    r = client.post("/payments/process", json={"amount": 50, "currency": "USD",
        "gateway": "stripe", "course_id": cid}, headers=headers)
    assert r.status_code == 200, r.text
    # El pago aprobado inscribe automáticamente (Observer); un enroll manual posterior es duplicado.
    assert client.post(f"/courses/{cid}/enroll", headers=headers).status_code == 409


# ------------------------------------------------------------------ unitarias

def test_duration_visitor_suma_todas_las_lecciones():
    content, *_ = _tree()
    visitor = DurationVisitor()
    content.accept(visitor)
    assert visitor.total_minutes == 45


def test_duration_visitor_arbol_vacio():
    visitor = DurationVisitor()
    CourseContent("Vacío").accept(visitor)
    assert visitor.total_minutes == 0


def test_progress_visitor_0_parcial_100():
    content, v1, v2, q1 = _tree()

    p0 = ProgressVisitor([])
    content.accept(p0)
    assert (p0.completed_lessons, p0.total_lessons, p0.percentage) == (0, 3, 0.0)

    partial = ProgressVisitor([v2.lesson_id])
    content.accept(partial)
    assert partial.percentage == pytest.approx(33.33)
    assert (partial.completed_minutes, partial.total_minutes) == (20, 45)

    full = ProgressVisitor([v1.lesson_id, v2.lesson_id, q1.lesson_id, "borrada"])
    content.accept(full)
    assert full.percentage == 100.0
    assert full.completed_lessons == 3     # ignora ids inexistentes
    assert full.completed_minutes == 45


def test_progress_visitor_sin_lecciones_no_divide_por_cero():
    visitor = ProgressVisitor(["x"])
    CourseContent("Vacío").accept(visitor)
    assert visitor.percentage == 0.0


def test_summary_visitor_cuenta_por_tipo_y_modulos():
    content, v1, _, q1 = _tree()
    visitor = ContentSummaryVisitor()
    content.accept(visitor)
    result = visitor.result()
    assert result["title"] == "Contenido de Python"
    assert result["total_modules"] == 2
    assert result["total_lessons"] == 3
    assert result["total_minutes"] == 45
    assert result["lessons_by_type"] == {"video": 2, "quiz": 1}
    fundamentos, evaluacion = result["syllabus"]
    assert fundamentos["title"] == "Fundamentos"
    assert fundamentos["duration_minutes"] == 30
    assert len(fundamentos["lessons"]) == 2
    assert fundamentos["lessons"][0]["lesson_id"] == v1.lesson_id
    assert evaluacion["lessons"][0]["type"] == "quiz"
    assert evaluacion["lessons"][0]["lesson_id"] == q1.lesson_id


def test_summary_visitor_modulos_anidados_suman_duracion():
    content = CourseContent("C")
    outer = content.add_module("Externo")
    inner = LessonModule("Interno")
    inner.add(VideoLesson("a", "a", VimeoStorageProvider(), duration_minutes=7))
    outer.add(inner)
    outer.add(VideoLesson("b", "b", VimeoStorageProvider(), duration_minutes=3))
    visitor = ContentSummaryVisitor()
    content.accept(visitor)
    (externo,) = visitor.result()["syllabus"]
    assert externo["duration_minutes"] == 10
    assert externo["modules"][0]["duration_minutes"] == 7
    assert visitor.result()["total_modules"] == 2


def test_export_syllabus_markdown():
    content, *_ = _tree()
    visitor = ExportSyllabusVisitor()
    content.accept(visitor)
    md = visitor.to_markdown()
    assert md.splitlines()[0] == "# Contenido de Python"
    assert "## Fundamentos" in md
    assert "(15 min)" in md


def test_doble_despacho_distingue_tipo_sin_isinstance():
    content, *_ = _tree()
    calls = []

    class Recorder(ContentVisitor):
        def visit_module(self, module):
            calls.append(("module", module.title))

        def visit_lesson(self, lesson):  # pragma: no cover - no debería usarse
            calls.append(("generic", lesson.title))

        def visit_video_lesson(self, lesson):
            calls.append(("video", lesson.title))

        def visit_quiz_lesson(self, lesson):
            calls.append(("quiz", lesson.title))

    content.accept(Recorder())
    assert calls == [("module", "Fundamentos"), ("video", "Intro"), ("video", "Tipos"),
                     ("module", "Evaluación"), ("quiz", "Quiz 1")]


def test_find_module_sin_isinstance_ignora_lecciones():
    content = CourseContent("C")
    content.add(VideoLesson("Fundamentos", "m", VimeoStorageProvider()))
    assert content.find_module("Fundamentos") is None
    module = content.add_module("Fundamentos")
    assert content.find_module("Fundamentos") is module


def test_to_dict_y_render_siguen_funcionando():
    content, v1, *_ = _tree()
    data = content.to_dict()
    assert data["items"][0]["items"][0]["lesson_id"] == v1.lesson_id
    assert data["items"][0]["items"][0]["duration_minutes"] == 10
    assert "Módulo: Fundamentos" in content.render_content()


# ------------------------------------------------------------------ proxy

def _proxy(course, student_id):
    return ProtectedContentProxy(
        real_factory=lambda: course.content, course=course,
        student_id=student_id, policy=EnrolledStudentPolicy(),
    )


def test_proxy_bloquea_visitante_sin_acceso():
    course = VideoCourse("c1", "Py", "Inst", 50)
    course.content.add_lesson("M", VideoLesson("a", "a", VimeoStorageProvider()))
    visitor = DurationVisitor()
    with pytest.raises(ContentAccessDenied):
        _proxy(course, "intruso").accept(visitor)
    assert visitor.total_minutes == 0


def test_proxy_delega_visitante_con_acceso():
    course = VideoCourse("c1", "Py", "Inst", 50)
    course.content.add_lesson("M", VideoLesson("a", "a", VimeoStorageProvider(), duration_minutes=12))
    course.enrolled_students.append("u1")
    visitor = DurationVisitor()
    _proxy(course, "u1").accept(visitor)
    assert visitor.total_minutes == 12


def test_clone_conserva_duracion_y_lesson_ids():
    course = VideoCourse("c1", "Py", "Inst", 0)
    lesson = VideoLesson("a", "a", VimeoStorageProvider(), duration_minutes=25)
    course.content.add_lesson("M", lesson)
    clone = course.clone()
    duration, index = DurationVisitor(), LessonIndexVisitor()
    clone.content.accept(duration)
    clone.content.accept(index)
    assert duration.total_minutes == 25
    assert index.lesson_ids == {lesson.lesson_id}


# ------------------------------------------------------------------ repositorio / use case

def test_progress_repository_idempotente():
    repo = InMemoryProgressRepository()
    assert repo.mark_completed("u", "c", "l1") is True
    assert repo.mark_completed("u", "c", "l1") is False
    assert repo.completed_lessons("u", "c") == {"l1"}
    assert repo.completed_lessons("otro", "c") == set()


def test_complete_lesson_use_case_publica_evento_solo_la_primera_vez():
    content, v1, *_ = _tree()
    published = []

    class Bus:
        def notify(self, event):
            published.append(event)

    use_case = CompleteLessonUseCase(
        InMemoryProgressRepository(), event_bus=Bus(),
        event_factory=lambda **kw: ("LESSON_COMPLETED", kw["lesson_id"]),
    )
    first = use_case.execute(content, "u1", "c1", v1.lesson_id)
    second = use_case.execute(content, "u1", "c1", v1.lesson_id)
    assert first["already_completed"] is False
    assert second["already_completed"] is True
    assert published == [("LESSON_COMPLETED", v1.lesson_id)]
    with pytest.raises(LessonNotFoundError):
        use_case.execute(content, "u1", "c1", "no-existe")


# ------------------------------------------------------------------ endpoints

def test_complete_lesson_sin_token_401(client):
    _, cid, l1, _ = _paid_course_with_lessons(client)
    assert client.post(f"/courses/{cid}/lessons/{l1}/complete").status_code == 401
    assert client.get(f"/courses/{cid}/progress/me").status_code == 401
    assert client.get(f"/courses/{cid}/content/summary").status_code == 401


def test_complete_lesson_no_inscrito_en_curso_de_pago_403(client):
    _, cid, l1, _ = _paid_course_with_lessons(client)
    alum = _login(client, "a@x.com", "student")
    assert client.post(f"/courses/{cid}/lessons/{l1}/complete", headers=alum).status_code == 403
    assert client.get(f"/courses/{cid}/progress/me", headers=alum).status_code == 403
    assert client.get(f"/courses/{cid}/content/summary", headers=alum).status_code == 403
    assert progress_repository.completed_lessons("cualquiera", cid) == set()


def test_complete_lesson_404_curso_o_leccion(client):
    _, cid, l1, _ = _paid_course_with_lessons(client)
    alum = _login(client, "a@x.com", "student")
    _enroll_paid(client, alum, cid)
    assert client.post(f"/courses/{cid}/lessons/no-existe/complete", headers=alum).status_code == 404
    assert client.post(f"/courses/no-existe/lessons/{l1}/complete", headers=alum).status_code == 404
    assert client.get("/courses/no-existe/progress/me", headers=alum).status_code == 404
    assert client.get("/courses/no-existe/content/summary", headers=alum).status_code == 404


def test_flujo_progreso_inscrito_200_e_idempotente(client):
    _, cid, l1, l2 = _paid_course_with_lessons(client)
    alum = _login(client, "a@x.com", "student")
    _enroll_paid(client, alum, cid)

    r = client.get(f"/courses/{cid}/progress/me", headers=alum)
    assert r.status_code == 200
    assert r.json()["percentage"] == 0.0 and r.json()["total_lessons"] == 2

    r = client.post(f"/courses/{cid}/lessons/{l1}/complete", headers=alum)
    assert r.status_code == 200
    body = r.json()
    assert body["already_completed"] is False
    assert body["progress"]["percentage"] == 50.0
    assert body["progress"]["completed_minutes"] == 30

    again = client.post(f"/courses/{cid}/lessons/{l1}/complete", headers=alum).json()
    assert again["already_completed"] is True
    assert again["progress"]["completed_lessons"] == 1

    client.post(f"/courses/{cid}/lessons/{l2}/complete", headers=alum)
    progress = client.get(f"/courses/{cid}/progress/me", headers=alum).json()
    assert progress["percentage"] == 100.0
    assert progress["completed_minutes"] == progress["total_minutes"] == 40
    assert sorted(progress["completed_lesson_ids"]) == sorted([l1, l2])


def test_progreso_es_por_estudiante(client):
    inst = _login(client, "i@x.com", "instructor")
    cid = _course(client, inst)            # curso gratuito: acceso abierto
    l1 = _lesson(client, inst, cid)
    a = _login(client, "a@x.com", "student")
    b = _login(client, "b@x.com", "student")
    client.post(f"/courses/{cid}/lessons/{l1}/complete", headers=a)
    assert client.get(f"/courses/{cid}/progress/me", headers=a).json()["percentage"] == 100.0
    assert client.get(f"/courses/{cid}/progress/me", headers=b).json()["percentage"] == 0.0


def test_summary_dueno_200(client):
    inst, cid, l1, l2 = _paid_course_with_lessons(client)
    r = client.get(f"/courses/{cid}/content/summary", headers=inst)
    assert r.status_code == 200
    body = r.json()
    assert body["course_id"] == cid
    assert body["total_minutes"] == 40
    assert body["total_modules"] == 2
    assert body["lessons_by_type"] == {"video": 1, "quiz": 1}
    assert "## M1" in body["syllabus_markdown"]
    assert course_repository.get_by_id(cid) is not None

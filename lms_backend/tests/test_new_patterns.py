
import pytest

from app.modules.courses.application.course_facade import CourseFacade
from app.modules.courses.domain.content_flyweight import (
    ContentMetadataFactory,
)
from app.modules.courses.domain.bridge import VideoLesson, VimeoStorageProvider, InteractiveQuizLesson
from app.modules.courses.domain.content_proxy import (
    ContentAccessDenied,
    EnrolledStudentPolicy,
    ProtectedContentProxy,
)
from app.modules.courses.application.dtos import CourseCreateDTO
from app.modules.courses.infrastructure.repository import InMemoryCourseRepository


def test_flyweight_reutiliza_metadatos():
    first = ContentMetadataFactory.get_metadata("video")
    second = ContentMetadataFactory.get_metadata("video")

    assert first is second
    assert first.content_type == "video"


def test_flyweight_rechaza_tipo_desconocido():
    with pytest.raises(ValueError):
        ContentMetadataFactory.get_metadata("unknown")



def test_flyweight_lecciones_comparten_metadatos():
    p = VimeoStorageProvider()
    a = VideoLesson("L1", "1", p)
    b = VideoLesson("L2", "2", p)
    q = InteractiveQuizLesson("Q", "3", p)
    assert a.metadata is b.metadata
    assert a.metadata is not q.metadata
    assert a.to_dict()["icon"] == "play-circle"


def _premium_course():
    repo = InMemoryCourseRepository()
    facade = CourseFacade(repo)
    course = facade.create_course(CourseCreateDTO(
        title="Py", instructor="A", price=10, course_type="video", premium=True))
    return facade, course


def test_proxy_bloquea_premium_sin_inscripcion():
    _, course = _premium_course()
    proxy = ProtectedContentProxy(lambda: course.content, course, "ana", EnrolledStudentPolicy())
    with pytest.raises(ContentAccessDenied):
        proxy.to_dict()


def test_proxy_permite_inscrito_y_es_perezoso():
    _, course = _premium_course()
    course.enrolled_students.append("ana")
    created = []
    def factory():
        created.append(1)
        return course.content
    proxy = ProtectedContentProxy(factory, course, "ana", EnrolledStudentPolicy())
    assert created == []          # lazy: aún no se creó el sujeto real
    proxy.to_dict()
    proxy.to_dict()
    assert created == [1]         # se crea una sola vez


def test_proxy_no_bloquea_no_premium():
    _, course = _premium_course()
    proxy = ProtectedContentProxy(lambda: course.content, course, None,
                                  EnrolledStudentPolicy(), requires_access=False)
    assert "title" in proxy.to_dict()


def test_facade_cuatro_operaciones():
    facade, course = _premium_course()
    assert len(facade.list_courses()) == 1
    clone = facade.clone_course(course.course_id, "Copia X")
    assert clone.course_id != course.course_id and clone.title == "Copia X"
    assert clone.content is not course.content          # deepcopy real
    facade.enroll_student(course.course_id, "ana")
    assert "ana" in facade.get_course(course.course_id).enrolled_students
    assert clone.enrolled_students == []


def _login(client, email, role, first="Ana", last="Perez"):
    client.post("/auth/register", json={"first_name": first, "last_name": last,
        "email": email, "password": "Secreta123", "role": role})
    r = client.post("/auth/login", json={"email": email, "password": "Secreta123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_endpoint_clone_y_proxy(client):
    inst = _login(client, "i@x.com", "instructor", "Ins", "Tructor")
    alum = _login(client, "a@x.com", "student")
    r = client.post("/courses/", json={"title":"Py","instructor":"A","price":100,
                                       "course_type":"video","premium":True})
    cid = r.json()["id"]
    assert r.json()["premium"] is True
    assert client.post(f"/courses/{cid}/clone", json={}).status_code == 201
    assert client.post(f"/courses/{cid}/content/lessons", json={
        "module_title":"M","title":"L","media_id":"1","provider":"vimeo"}).status_code == 201
    assert client.get(f"/courses/{cid}/content").status_code == 401
    assert client.get(f"/courses/{cid}/content", headers=alum).status_code == 403
    assert client.get(f"/courses/{cid}/content", headers=inst).status_code == 200
    client.post(f"/courses/{cid}/enroll", json={"student_name": "Ana Perez"})
    assert client.get(f"/courses/{cid}/content", headers=alum).status_code == 200

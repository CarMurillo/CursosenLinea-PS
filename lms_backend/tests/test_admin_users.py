"""Administración de usuarios: listas por rol, ficha detallada, registro por
el admin y suspensión/reactivación."""

from app.main import app
from app.modules.auth.application.dtos import UserRegisterDTO
from app.modules.auth.application.use_cases import RegisterUserUseCase
from app.modules.auth.domain.models import Role
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository

PWD = "Secreta123"


def _login(client, email, role):
    client.post("/auth/register", json={"first_name": email.split("@")[0], "last_name": "X",
                "email": email, "password": PWD, "role": role})
    r = client.post("/auth/login", json={"email": email, "password": PWD})
    assert r.status_code == 200, r.text
    body = r.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]["user_id"]


def _admin(client):
    db = next(app.dependency_overrides[get_db]())
    RegisterUserUseCase(SqlAlchemyUserRepository(db)).execute(UserRegisterDTO(
        first_name="Ad", last_name="Min", email="admin@x.com", password=PWD, role=Role.ADMIN))
    r = client.post("/auth/login", json={"email": "admin@x.com", "password": PWD})
    body = r.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]["user_id"]


def _course(client, inst, title, lessons=2, **extra):
    r = client.post("/courses/", json={"title": title, "price": 0, "course_type": "video",
                                       **extra}, headers=inst)
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    for i in range(lessons):
        assert client.post(f"/courses/{cid}/content/lessons", json={
            "module_title": "M1", "title": f"L{i}", "media_id": f"m{i}", "provider": "vimeo",
        }, headers=inst).status_code == 201
    return cid


def _complete(client, alum, cid, count):
    summary = client.get(f"/courses/{cid}/content/summary", headers=alum).json()
    ids = [l["lesson_id"] for m in summary["syllabus"] for l in m["lessons"]][:count]
    for lid in ids:
        assert client.post(f"/courses/{cid}/lessons/{lid}/complete", headers=alum).status_code == 200


def test_listas_separadas_por_rol(client):
    admin, _ = _admin(client)
    _login(client, "s1@x.com", "student")
    _login(client, "s2@x.com", "student")
    _login(client, "i1@x.com", "instructor")

    students = client.get("/users/?role=student", headers=admin).json()
    instructors = client.get("/users/?role=instructor", headers=admin).json()
    assert {u["email"] for u in students} == {"s1@x.com", "s2@x.com"}
    assert {u["email"] for u in instructors} == {"i1@x.com"}
    assert all("created_at" in u and "is_active" in u for u in students)
    assert client.get("/users/?role=otro", headers=admin).status_code == 422


def test_rutas_de_administracion_son_solo_para_admin(client):
    alum, alum_id = _login(client, "s@x.com", "student")
    inst, _ = _login(client, "i@x.com", "instructor")
    for headers in (alum, inst):
        assert client.get("/users/?role=student", headers=headers).status_code == 403
        assert client.get(f"/users/{alum_id}/detail", headers=headers).status_code == 403
        assert client.patch(f"/users/{alum_id}/status", json={"is_active": False},
                            headers=headers).status_code == 403
        assert client.post("/users/", json={"first_name": "N", "last_name": "N",
                           "email": "n@x.com", "password": PWD, "role": "student"},
                           headers=headers).status_code == 403
    assert client.get(f"/users/{alum_id}/detail").status_code == 401


def test_ficha_del_estudiante_cursos_estado_y_certificados(client):
    admin, _ = _admin(client)
    inst, _ = _login(client, "i@x.com", "instructor")
    alum, alum_id = _login(client, "s@x.com", "student")

    c_done = _course(client, inst, "Terminado", certificate=True)
    c_started = _course(client, inst, "Iniciado")
    c_new = _course(client, inst, "Sin iniciar")
    for cid in (c_done, c_started, c_new):
        assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 200
    _complete(client, alum, c_done, 2)
    _complete(client, alum, c_started, 1)

    # Certificado vía evaluación aprobada (Observer).
    a = client.post("/assessments", json={"course_id": c_done, "title": "Final",
                    "passing_score": 50, "max_attempts": 1}, headers=inst).json()
    client.post(f"/assessments/{a['id']}/questions", json={
        "text": "¿2+2?", "options": ["3", "4"], "correct_option": 1}, headers=inst)
    client.post(f"/assessments/{a['id']}/publish", headers=inst)
    qid = client.get(f"/assessments/{a['id']}", headers=inst).json()["questions"][0]["question_id"]
    assert client.post(f"/assessments/{a['id']}/attempts", json={"answers": {qid: 1}},
                       headers=alum).status_code == 201

    r = client.get(f"/users/{alum_id}/detail", headers=admin)
    assert r.status_code == 200
    detail = r.json()
    assert detail["role"] == "student" and "instructor" not in detail
    st = detail["student"]
    assert st["enrolled_count"] == 3
    assert (st["completed_count"], st["in_progress_count"], st["not_started_count"]) == (1, 1, 1)
    status = {c["title"]: (c["status"], c["progress"], c["has_certificate"]) for c in st["courses"]}
    assert status["Terminado"] == ("terminado", 100.0, True)
    assert status["Iniciado"] == ("iniciado", 50.0, False)
    assert status["Sin iniciar"] == ("sin_iniciar", 0.0, False)
    assert st["certificate_count"] == 1
    assert st["certificates"][0]["course_id"] == c_done
    assert st["payments"] == []


def test_ficha_del_instructor_cursos_y_alumnos(client):
    admin, _ = _admin(client)
    inst, inst_id = _login(client, "i@x.com", "instructor")
    alum, _ = _login(client, "s@x.com", "student")
    cid = _course(client, inst, "Curso A")
    _course(client, inst, "Curso B")
    client.post(f"/courses/{cid}/enroll", headers=alum)

    detail = client.get(f"/users/{inst_id}/detail", headers=admin).json()
    assert detail["instructor"]["course_count"] == 2
    assert detail["instructor"]["student_count"] == 1
    assert client.get("/users/no-existe/detail", headers=admin).status_code == 404


def test_suspender_bloquea_token_y_login_y_reactivar_lo_devuelve(client):
    admin, _ = _admin(client)
    alum, alum_id = _login(client, "s@x.com", "student")
    assert client.get("/courses/me/enrolled", headers=alum).status_code == 200

    r = client.patch(f"/users/{alum_id}/status", json={"is_active": False}, headers=admin)
    assert r.status_code == 200 and r.json()["is_active"] is False
    # Efecto inmediato: el token vigente deja de servir y el login falla.
    assert client.get("/courses/me/enrolled", headers=alum).status_code == 401
    assert client.post("/auth/login", json={"email": "s@x.com", "password": PWD}).status_code == 401

    r = client.patch(f"/users/{alum_id}/status", json={"is_active": True}, headers=admin)
    assert r.json()["is_active"] is True
    assert client.post("/auth/login", json={"email": "s@x.com", "password": PWD}).status_code == 200


def test_suspender_instructor_y_limites(client):
    admin, admin_id = _admin(client)
    _, inst_id = _login(client, "i@x.com", "instructor")
    assert client.patch(f"/users/{inst_id}/status", json={"is_active": False},
                        headers=admin).json()["is_active"] is False
    # No se suspende a sí mismo ni a otro admin; usuario inexistente -> 404.
    assert client.patch(f"/users/{admin_id}/status", json={"is_active": False},
                        headers=admin).status_code == 400
    assert client.patch("/users/no-existe/status", json={"is_active": False},
                        headers=admin).status_code == 404


def test_admin_registra_estudiantes_e_instructores(client):
    admin, _ = _admin(client)
    body = {"first_name": "Nueva", "last_name": "Alumna", "email": "Nueva@X.com",
            "password": PWD, "role": "student"}
    r = client.post("/users/", json=body, headers=admin)
    assert r.status_code == 201
    assert r.json()["email"] == "nueva@x.com" and r.json()["role"] == "student"
    # La cuenta creada por el admin puede iniciar sesión.
    assert client.post("/auth/login", json={"email": "nueva@x.com",
                       "password": PWD}).status_code == 200

    r = client.post("/users/", json={**body, "email": "prof@x.com", "role": "instructor"},
                    headers=admin)
    assert r.status_code == 201 and r.json()["role"] == "instructor"
    assert client.post("/users/", json=body, headers=admin).status_code == 409
    assert client.post("/users/", json={**body, "email": "otro@x.com", "role": "admin"},
                       headers=admin).status_code == 400
    assert client.post("/users/", json={**body, "email": "corta@x.com", "password": "123"},
                       headers=admin).status_code == 422


# ------------------------------------------------------------------ eliminar

def test_eliminar_estudiante_lo_quita_de_cursos_e_invalida_su_sesion(client):
    admin, _ = _admin(client)
    inst, _ = _login(client, "i@x.com", "instructor")
    alum, alum_id = _login(client, "s@x.com", "student")
    cid = _course(client, inst, "Curso")
    client.post(f"/courses/{cid}/enroll", headers=alum)

    r = client.delete(f"/users/{alum_id}", headers=admin)
    assert r.status_code == 200
    assert r.json()["deleted"]["email"] == "s@x.com"
    assert r.json()["removed_enrollments"] == 1

    assert client.get(f"/users/{alum_id}/detail", headers=admin).status_code == 404
    assert "s@x.com" not in {u["email"] for u in
                             client.get("/users/?role=student", headers=admin).json()}
    # Su token y su login dejan de servir; el curso ya no lo cuenta.
    assert client.get("/courses/me/enrolled", headers=alum).status_code == 401
    assert client.post("/auth/login", json={"email": "s@x.com", "password": PWD}).status_code == 401
    course = next(c for c in client.get("/courses/").json() if c["id"] == cid)
    assert alum_id not in course.get("enrolled_students", [])
    # El correo queda libre para registrarse de nuevo.
    assert client.post("/auth/register", json={"first_name": "S", "last_name": "X",
                       "email": "s@x.com", "password": PWD, "role": "student"}).status_code == 201


def test_eliminar_instructor_sin_cursos_si_con_cursos_no(client):
    admin, _ = _admin(client)
    _, libre_id = _login(client, "libre@x.com", "instructor")
    inst, inst_id = _login(client, "i@x.com", "instructor")
    _course(client, inst, "Curso con dueño")

    assert client.delete(f"/users/{libre_id}", headers=admin).status_code == 200
    r = client.delete(f"/users/{inst_id}", headers=admin)
    assert r.status_code == 409 and "Curso con dueño" in r.json()["detail"]
    assert client.get(f"/users/{inst_id}/detail", headers=admin).status_code == 200


def test_eliminar_limites_y_permisos(client):
    admin, admin_id = _admin(client)
    alum, alum_id = _login(client, "s@x.com", "student")
    inst, _ = _login(client, "i@x.com", "instructor")
    assert client.delete(f"/users/{alum_id}").status_code == 401
    assert client.delete(f"/users/{alum_id}", headers=alum).status_code == 403
    assert client.delete(f"/users/{alum_id}", headers=inst).status_code == 403
    assert client.delete(f"/users/{admin_id}", headers=admin).status_code == 400
    assert client.delete("/users/no-existe", headers=admin).status_code == 404

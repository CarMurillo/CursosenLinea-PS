# Cambio de contrato (Fase 1, B2/B4/E3):
# - Crear curso exige token de instructor/admin; el instructor sale del token.
# - La inscripción usa el usuario autenticado (ya no `student_name` en el cuerpo).
# - Un curso con precio > 0 o premium exige pago aprobado, por eso el curso del
#   test de Observer pasa a ser gratuito (price=0).


def _login(client, email, role, first="Ana", last="Perez"):
    client.post("/auth/register", json={"first_name": first, "last_name": last,
        "email": email, "password": "Secreta123", "role": role})
    r = client.post("/auth/login", json={"email": email, "password": "Secreta123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_publish_video_course_uses_factory_method(client):
    inst = _login(client, "carlos@x.com", "instructor", "Carlos", "Murillo")
    response = client.post(
        "/courses/",
        json={
            "title": "Arquitectura de Software",
            "instructor": "Carlos Murillo",
            "price": 49.9,
            "course_type": "video",
        },
        headers=inst,
    )
    assert response.status_code == 201
    course = response.json()
    assert course["type"] == "Video bajo demanda"


def test_publish_live_course_uses_factory_method(client):
    inst = _login(client, "carlos@x.com", "instructor", "Carlos", "Murillo")
    response = client.post(
        "/courses/",
        json={
            "title": "Taller en vivo de patrones GoF",
            "instructor": "Carlos Murillo",
            "price": 0,
            "course_type": "live",
        },
        headers=inst,
    )
    assert response.status_code == 201
    assert response.json()["type"] == "Clase en Vivo (Videoconferencia)"


def test_enroll_student_notifies_observers(client, capsys):
    inst = _login(client, "ana@x.com", "instructor", "Ana", "Gomez")
    alum = _login(client, "luis@x.com", "student", "Luis", "Perez")
    publish_response = client.post(
        "/courses/",
        json={
            "title": "Fundamentos de Bases de Datos",
            "price": 0,
            "course_type": "video",
        },
        headers=inst,
    )
    course_id = publish_response.json()["id"]

    response = client.post(f"/courses/{course_id}/enroll", headers=alum)

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # El patrón Observer debe disparar las notificaciones registradas.
    captured = capsys.readouterr()
    assert "Luis Perez" in captured.out


def test_enroll_in_nonexistent_course_returns_404(client):
    alum = _login(client, "ana@x.com", "student")
    response = client.post("/courses/no-existe/enroll", headers=alum)
    assert response.status_code == 404

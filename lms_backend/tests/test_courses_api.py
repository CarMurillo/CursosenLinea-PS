def test_publish_video_course_uses_factory_method(client):
    response = client.post(
        "/courses/",
        json={
            "title": "Arquitectura de Software",
            "instructor": "Carlos Murillo",
            "price": 49.9,
            "course_type": "video",
        },
    )
    assert response.status_code == 201
    course = response.json()
    assert course["type"] == "Video bajo demanda"


def test_publish_live_course_uses_factory_method(client):
    response = client.post(
        "/courses/",
        json={
            "title": "Taller en vivo de patrones GoF",
            "instructor": "Carlos Murillo",
            "price": 0,
            "course_type": "live",
        },
    )
    assert response.status_code == 201
    assert response.json()["type"] == "Clase en Vivo (Videoconferencia)"


def test_enroll_student_notifies_observers(client, capsys):
    publish_response = client.post(
        "/courses/",
        json={
            "title": "Fundamentos de Bases de Datos",
            "instructor": "Ana Gomez",
            "price": 19.99,
            "course_type": "video",
        },
    )
    course_id = publish_response.json()["id"]

    response = client.post(f"/courses/{course_id}/enroll", json={"student_name": "Luis Perez"})

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # El patrón Observer debe disparar las notificaciones registradas.
    captured = capsys.readouterr()
    assert "Luis Perez" in captured.out


def test_enroll_in_nonexistent_course_returns_404(client):
    response = client.post("/courses/no-existe/enroll", json={"student_name": "Ana"})
    assert response.status_code == 404
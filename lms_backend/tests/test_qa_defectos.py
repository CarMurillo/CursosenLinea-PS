"""
Defectos reales encontrados por QA (Fase 5). Cada prueba describe el
comportamiento CORRECTO. Nacieron como `xfail(strict=True)`; en la Fase 6
se corrigieron QA-1 a QA-5 y se quitaron las marcas: ahora son pruebas de
regresión normales.
"""

import pytest

from app.modules.payments.domain.adapter import StripePaymentAdapter

PWD = "Secreta123"
JSON = {"Content-Type": "application/json"}


def _login(client, email, role="student"):
    r = client.post("/auth/register", json={
        "first_name": "Ana", "last_name": "Perez", "email": email,
        "password": PWD, "role": role})
    assert r.status_code == 201, r.text
    r = client.post("/auth/login", json={"email": email, "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# --------------------------------------------------------------------- QA-1

def test_qa1_precio_infinito_rechazado_y_catalogo_sigue_vivo(client):
    inst = _login(client, "i@qa.com", "instructor")
    r = client.post("/courses/", headers={**inst, **JSON},
                    content='{"title": "t", "price": 1e999, "course_type": "video"}')
    assert r.status_code == 422
    assert client.get("/courses/").status_code == 200


@pytest.mark.parametrize("gateway", ["stripe", "wompi"])
def test_qa1_monto_infinito_responde_422(client, gateway):
    inst = _login(client, "i@qa.com", "instructor")
    alum = _login(client, "a@qa.com")
    cid = client.post("/courses/", json={"title": "P", "price": 10,
                      "course_type": "video"}, headers=inst).json()["id"]
    body = '{"amount": 1e999, "currency": "USD", "gateway": "%s", "course_id": "%s"}' \
        % (gateway, cid)
    r = client.post("/payments/process", headers={**alum, **JSON}, content=body)
    assert r.status_code == 422


def test_qa1_puntaje_infinito_responde_422(client):
    inst = _login(client, "i@qa.com", "instructor")
    cid = client.post("/courses/", json={"title": "P", "price": 0,
                      "course_type": "video"}, headers=inst).json()["id"]
    aid = client.post("/assessments", json={"course_id": cid, "title": "Q"},
                      headers=inst).json()["id"]
    r = client.post(f"/assessments/{aid}/questions", headers={**inst, **JSON},
                    content='{"text": "t", "options": ["a","b"], '
                            '"correct_option": 0, "points": 1e999}')
    assert r.status_code == 422
    assert client.get(f"/assessments/{aid}", headers=inst).status_code == 200


# --------------------------------------------------------------------- QA-2

def test_qa2_premium_precio_cero_es_adquirible_o_se_rechaza(client):
    inst = _login(client, "i@qa.com", "instructor")
    alum = _login(client, "a@qa.com")
    r = client.post("/courses/", json={"title": "P0", "price": 0,
                    "course_type": "video", "premium": True}, headers=inst)
    if r.status_code in (400, 422):
        return  # corrección válida: no se permite crear premium sin precio
    course = r.json()
    # Flujo del front (StudentCourses.jsx): paga amount = course.price.
    pay = client.post("/payments/process", json={
        "amount": course["price"], "currency": "USD", "gateway": "stripe",
        "course_id": course["id"]}, headers=alum)
    enroll = client.post(f"/courses/{course['id']}/enroll", headers=alum)
    assert pay.status_code == 200 or enroll.status_code == 200


# --------------------------------------------------------------------- QA-3

def test_qa3_no_cobra_curso_en_el_que_ya_esta_inscrito(client):
    inst = _login(client, "i@qa.com", "instructor")
    alum = _login(client, "a@qa.com")
    cid = client.post("/courses/", json={"title": "Free", "price": 0,
                      "course_type": "video"}, headers=inst).json()["id"]
    assert client.post(f"/courses/{cid}/enroll", headers=alum).status_code == 200
    r = client.post("/payments/process", json={
        "amount": 5, "currency": "USD", "gateway": "stripe", "course_id": cid},
        headers=alum)
    assert r.status_code in (400, 409)
    assert client.get("/payments/me", headers=alum).json() == []


# --------------------------------------------------------------------- QA-4

class _SpySDK:
    def __init__(self):
        self.cents = None

    def create_charge(self, amount_in_cents, currency_code, email):
        self.cents = amount_in_cents
        return {"id": f"ch_{amount_in_cents}", "status": "succeeded"}


def test_qa4_stripe_convierte_a_centavos_sin_truncar():
    sdk = _SpySDK()
    StripePaymentAdapter(sdk).process_payment(19.99, "USD", "a@qa.com")
    assert sdk.cents == 1999


# --------------------------------------------------------------------- QA-5

def test_qa5_registro_rechaza_correo_invalido(client):
    r = client.post("/auth/register", json={
        "first_name": "A", "last_name": "B", "email": "noesuncorreo",
        "password": PWD, "role": "student"})
    assert r.status_code == 422


def test_qa5_correo_duplicado_sin_distinguir_mayusculas(client):
    base = {"first_name": "A", "last_name": "B", "password": PWD, "role": "student"}
    assert client.post("/auth/register", json={**base, "email": "Dup@qa.com"}).status_code == 201
    r = client.post("/auth/register", json={**base, "email": "dup@qa.com"})
    assert r.status_code == 409


def test_qa5_registro_rechaza_password_vacia(client):
    r = client.post("/auth/register", json={
        "first_name": "", "last_name": "", "email": "e@qa.com",
        "password": "", "role": "student"})
    assert r.status_code == 422

"""Datos de demostración del LMS (para la demo del parcial).

POR QUÉ ES UN CLIENTE HTTP: cursos, pagos, evaluaciones, clases y progreso
viven en repositorios EN MEMORIA dentro del proceso de uvicorn. Un script que
importe la app en otro proceso (o use TestClient) llenaría SU propia memoria
y el servidor no vería nada. Por eso este script habla con el servidor que ya
está corriendo usando solo `urllib` (biblioteca estándar) y los mismos
endpoints que usa el frontend (pasa por casos de uso, Observer, State, etc.).

La única excepción es el ADMIN: el registro público no permite el rol admin,
así que se crea directamente en la BD de usuarios (la misma `DATABASE_URL`
que usa el servidor, por defecto ./app.db) con `RegisterUserUseCase`.

Uso (desde lms_backend/, con el servidor arriba):
    ./venv/Scripts/python -m uvicorn app.main:app --reload      # terminal 1
    ./venv/Scripts/python scripts/seed.py                       # terminal 2
    ./venv/Scripts/python scripts/seed.py --base-url http://127.0.0.1:8000

Idempotente: los usuarios se reutilizan si ya existen (BD persistente); los
cursos se reutilizan si el instructor ya tiene uno con el mismo título. Al
REINICIAR uvicorn se pierden los datos en memoria (no los usuarios): vuelve a
ejecutar el seed para reconstruir la demo.

Cuentas de demo (contraseña común: Demo12345):
    admin@lms.demo       admin
    instructor@lms.demo  instructor
    estudiante@lms.demo  student

Crea: curso gratuito "Fundamentos de Python" (2 módulos, 3 lecciones con
duración, estudiante inscrito con 1 lección completada) y curso premium con
certificado "Arquitectura de Software con Patrones" (precio 49.9, 3 lecciones,
evaluación publicada de 2 preguntas y una clase en vivo ya grabada). El
estudiante NO queda inscrito en el premium: en la demo paga (Stripe/Wompi),
se inscribe automáticamente, completa lecciones, rinde y obtiene certificado.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

DEMO_PASSWORD = "Demo12345"
ADMIN = {"first_name": "Ada", "last_name": "Admin", "email": "admin@lms.demo"}
INSTRUCTOR = {"first_name": "Iván", "last_name": "Instructor",
              "email": "instructor@lms.demo", "role": "instructor",
              "specialization": "Arquitectura de software"}
STUDENT = {"first_name": "Sofía", "last_name": "Estudiante",
           "email": "estudiante@lms.demo", "role": "student"}

FREE_COURSE = {"title": "Fundamentos de Python", "price": 0, "course_type": "video"}
PREMIUM_COURSE = {"title": "Arquitectura de Software con Patrones", "price": 49.9,
                  "course_type": "video", "premium": True, "certificate": True}

FREE_LESSONS = [
    ("Introducción", "Instalación y primer programa", "video", "vimeo", 12),
    ("Introducción", "Variables y tipos", "video", "s3", 18),
    ("Práctica", "Quiz de repaso", "quiz", "vimeo", 10),
]
PREMIUM_LESSONS = [
    ("Patrones de comportamiento", "Observer con eventos de dominio", "video", "vimeo", 25),
    ("Patrones de comportamiento", "State en evaluaciones", "video", "s3", 20),
    ("Patrones estructurales", "Visitor sobre Composite", "quiz", "vimeo", 15),
]
ASSESSMENT = {"title": "Parcial de patrones", "description": "Observer, State y Visitor",
              "passing_score": 60, "max_attempts": 3}
QUESTIONS = [
    {"text": "¿Qué patrón desacopla al publicador de sus suscriptores?",
     "options": ["Singleton", "Observer", "Builder"], "correct_option": 1, "points": 5},
    {"text": "¿Qué patrón agrega operaciones a un Composite sin modificarlo?",
     "options": ["Visitor", "Adapter", "Proxy"], "correct_option": 0, "points": 5},
]
LIVE_SESSION = {"title": "Clase en vivo: patrones en la práctica",
                "duration_minutes": 60}

# request(method, path, body, token) -> (status_code, json_body)
Requester = Callable[[str, str, Optional[dict], Optional[str]], Tuple[int, Any]]


class SeedError(RuntimeError):
    pass


def urllib_requester(base_url: str) -> Requester:
    base = base_url.rstrip("/")

    def request(method, path, body=None, token=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(base + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return resp.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            raw = error.read().decode("utf-8")
            try:
                return error.code, json.loads(raw) if raw else None
            except ValueError:
                return error.code, raw

    return request


def _expect(result, *ok, what=""):
    status, body = result
    if status not in ok:
        raise SeedError(f"{what}: HTTP {status} {body}")
    return body


def ensure_admin(session_factory=None) -> bool:
    """Crea el admin directo en la BD de usuarios. True si lo creó."""
    from app.modules.auth.application.dtos import UserRegisterDTO
    from app.modules.auth.application.use_cases import RegisterUserUseCase
    from app.modules.auth.domain.models import Role
    from app.shared.infrastructure.user_repository import SqlAlchemyUserRepository

    if session_factory is None:
        from app.shared.infrastructure.database import SessionLocal, init_db
        init_db()
        session_factory = SessionLocal

    db = session_factory()
    try:
        repo = SqlAlchemyUserRepository(db)
        if repo.get_by_email(ADMIN["email"]):
            return False
        RegisterUserUseCase(repo).execute(UserRegisterDTO(
            **ADMIN, password=DEMO_PASSWORD, role=Role.ADMIN))
        return True
    finally:
        db.close()


def _login(request: Requester, user: dict) -> dict:
    status, _ = request("POST", "/auth/register", {**user, "password": DEMO_PASSWORD}, None)
    if status not in (201, 409):
        raise SeedError(f"registro de {user['email']}: HTTP {status}")
    body = _expect(request("POST", "/auth/login",
                           {"email": user["email"], "password": DEMO_PASSWORD}, None),
                   200, what=f"login {user['email']}")
    return {"token": body["access_token"], "user_id": body["user"]["user_id"]}


def _ensure_course(request, inst, course, lessons, log):
    existing = _expect(request("GET", "/courses/", None, None), 200, what="listar cursos")
    for c in existing:
        if c["title"] == course["title"] and c.get("instructor_id") == inst["user_id"]:
            log(f"= curso existente: {course['title']} ({c['id']})")
            return c["id"], False
    created = _expect(request("POST", "/courses/", course, inst["token"]), 201,
                      what=f"crear curso {course['title']}")
    cid = created["id"]
    for module, title, kind, provider, minutes in lessons:
        _expect(request("POST", f"/courses/{cid}/content/lessons", {
            "module_title": module, "title": title, "media_id": "demo-" + "-".join(title.lower().split()),
            "provider": provider, "lesson_type": kind, "duration_minutes": minutes,
        }, inst["token"]), 201, what=f"lección {title}")
    log(f"+ curso creado: {course['title']} ({cid}) con {len(lessons)} lecciones")
    return cid, True


def run_seed(request: Requester, *, create_admin: Callable[[], bool] = ensure_admin,
             log: Callable[[str], None] = print) -> dict:
    admin_created = create_admin()
    log(("+ " if admin_created else "= ") + f"admin {ADMIN['email']}")
    inst = _login(request, INSTRUCTOR)
    alum = _login(request, STUDENT)
    log(f"= instructor {INSTRUCTOR['email']} / estudiante {STUDENT['email']}")

    free_id, _ = _ensure_course(request, inst, FREE_COURSE, FREE_LESSONS, log)
    premium_id, premium_new = _ensure_course(
        request, inst, PREMIUM_COURSE, PREMIUM_LESSONS, log)

    # Estudiante inscrito en el gratuito con una lección completada.
    _expect(request("POST", f"/courses/{free_id}/enroll", None, alum["token"]),
            200, 409, what="inscripción gratuita")
    summary = _expect(request("GET", f"/courses/{free_id}/content/summary", None,
                              alum["token"]), 200, what="resumen")
    first_lesson = summary["syllabus"][0]["lessons"][0]["lesson_id"]
    _expect(request("POST", f"/courses/{free_id}/lessons/{first_lesson}/complete",
                    None, alum["token"]), 200, what="completar lección")

    assessment_id = None
    session_id = None
    if premium_new:
        a = _expect(request("POST", "/assessments", {**ASSESSMENT, "course_id": premium_id},
                            inst["token"]), 201, what="crear evaluación")
        assessment_id = a["id"]
        for q in QUESTIONS:
            _expect(request("POST", f"/assessments/{assessment_id}/questions", q,
                            inst["token"]), 201, what="pregunta")
        _expect(request("POST", f"/assessments/{assessment_id}/publish", None,
                        inst["token"]), 200, what="publicar evaluación")
        log(f"+ evaluación publicada: {ASSESSMENT['title']} ({assessment_id})")

        s = _expect(request("POST", "/live-sessions", {**LIVE_SESSION, "course_id": premium_id},
                            inst["token"]), 201, what="programar clase")
        session_id = s["id"]
        _expect(request("POST", f"/live-sessions/{session_id}/start", None, inst["token"]),
                200, what="iniciar clase")
        ended = _expect(request("POST", f"/live-sessions/{session_id}/end", None,
                                inst["token"]), 200, what="terminar clase")
        log(f"+ clase grabada: {ended['recording_url']}")

    result = {
        "password": DEMO_PASSWORD,
        "admin": ADMIN["email"],
        "instructor": INSTRUCTOR["email"],
        "student": STUDENT["email"],
        "free_course_id": free_id,
        "premium_course_id": premium_id,
        "assessment_id": assessment_id,
        "live_session_id": session_id,
    }
    log("Listo. Contraseña de las cuentas demo: " + DEMO_PASSWORD)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Carga datos de demo en el LMS.")
    parser.add_argument("--base-url", default=os.getenv("LMS_API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--skip-admin", action="store_true",
                        help="No crear el admin en la BD local.")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):   # tildes legibles en consolas Windows
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    request = urllib_requester(args.base_url)
    try:
        request("GET", "/health", None, None)
    except urllib.error.URLError as error:
        print(f"No se pudo conectar con {args.base_url}: {error.reason}. "
              "¿Está corriendo uvicorn?", file=sys.stderr)
        return 1
    try:
        run_seed(request, create_admin=(lambda: False) if args.skip_admin else ensure_admin)
    except SeedError as error:
        print(f"Seed falló: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

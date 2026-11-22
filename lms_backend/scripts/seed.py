"""Datos de demostración del LMS (para la presentación).

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
cursos se reutilizan si el instructor ya tiene uno con el mismo título. Las
evaluaciones, clases y la actividad de los estudiantes (pagos, lecciones,
intentos) de un curso solo se crean cuando ese curso se crea en esta
ejecución, así que correrlo dos veces no duplica nada. Al REINICIAR uvicorn
se pierden los datos en memoria (no los usuarios): vuelve a ejecutar el seed.

Cuentas de demo (contraseña común: Demo12345):
    admin@lms.demo        admin
    instructor@lms.demo   instructor  (Iván: 3 cursos)
    laura@lms.demo        instructor  (Laura: 3 cursos)
    estudiante@lms.demo   student     Sofía: inscrita en Python con 1 lección.
                                      NO está inscrita en el premium: en la
                                      demo paga, rinde y obtiene certificado.
    carlos@lms.demo       student     Pagó Arquitectura (Stripe), completó
                                      todo, aprobó -> certificado.
    valentina@lms.demo    student     Pagó Arquitectura (Wompi) y cursó
                                      Ciencia de Datos -> 2 certificados.
    lucia@lms.demo        student     Pagó Diseño de APIs (Wompi) y reprobó
                                      -> recomendaciones de "refuerzo".
    mateo@lms.demo        student     Sin cursos -> "gratis para empezar".

Patrones que quedan visibles: Adapter + Template Method (pagos Stripe/Wompi),
Observer (auto-inscripción, notificaciones, auditoría, certificados), State
(evaluaciones publicada/borrador, clases grabada/programada), Visitor
(progreso y resumen), Strategy (recomendaciones distintas por estudiante).
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

DEMO_PASSWORD = "Demo12345"

# ----------------------------------------------------------------- usuarios
ADMIN = {"first_name": "Ada", "last_name": "Admin", "email": "admin@lms.demo"}
INSTRUCTOR = {"first_name": "Iván", "last_name": "Instructor",
              "email": "instructor@lms.demo", "role": "instructor",
              "specialization": "Arquitectura de software"}
INSTRUCTOR_2 = {"first_name": "Laura", "last_name": "Datos",
                "email": "laura@lms.demo", "role": "instructor",
                "specialization": "Ciencia de datos"}
STUDENT = {"first_name": "Sofía", "last_name": "Estudiante",
           "email": "estudiante@lms.demo", "role": "student"}
CARLOS = {"first_name": "Carlos", "last_name": "Certificado",
          "email": "carlos@lms.demo", "role": "student"}
VALENTINA = {"first_name": "Valentina", "last_name": "Destacada",
             "email": "valentina@lms.demo", "role": "student"}
LUCIA = {"first_name": "Lucía", "last_name": "Refuerzo",
         "email": "lucia@lms.demo", "role": "student"}
MATEO = {"first_name": "Mateo", "last_name": "Nuevo",
         "email": "mateo@lms.demo", "role": "student"}

# ------------------------------------------------------------------ cursos
FREE_COURSE = {"title": "Fundamentos de Python", "price": 0, "course_type": "video"}
PREMIUM_COURSE = {"title": "Arquitectura de Software con Patrones", "price": 49.9,
                  "course_type": "video", "premium": True, "certificate": True}
API_COURSE = {"title": "Diseño de APIs con FastAPI", "price": 39.9,
              "course_type": "video", "premium": True, "certificate": True}
DATA_COURSE = {"title": "Introducción a Ciencia de Datos", "price": 0,
               "course_type": "video", "certificate": True}
ML_COURSE = {"title": "Machine Learning en Vivo", "price": 59.9,
             "course_type": "live", "premium": True, "certificate": True}
SQL_COURSE = {"title": "SQL para Análisis de Datos", "price": 0, "course_type": "video"}

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
API_LESSONS = [
    ("Fundamentos", "Rutas y validación con Pydantic", "video", "vimeo", 22),
    ("Fundamentos", "Dependencias e inyección", "video", "s3", 18),
    ("Seguridad", "Autenticación con JWT", "video", "vimeo", 25),
    ("Seguridad", "Quiz de seguridad", "quiz", "s3", 10),
]
DATA_LESSONS = [
    ("Bases", "¿Qué es la ciencia de datos?", "video", "vimeo", 15),
    ("Bases", "Pandas en 20 minutos", "video", "s3", 20),
    ("Práctica", "Quiz de pandas", "quiz", "vimeo", 10),
]
ML_LESSONS = [
    ("Teoría", "Regresión lineal", "video", "vimeo", 30),
    ("Teoría", "Árboles de decisión", "video", "s3", 30),
    ("Práctica", "Quiz de modelos", "quiz", "vimeo", 15),
]
SQL_LESSONS = [
    ("Consultas", "SELECT, WHERE y ORDER BY", "video", "vimeo", 14),
    ("Consultas", "JOIN entre tablas", "video", "s3", 20),
    ("Agregaciones", "GROUP BY y HAVING", "video", "vimeo", 16),
]

# ------------------------------------------------------------- evaluaciones
ASSESSMENT = {"title": "Parcial de patrones", "description": "Observer, State y Visitor",
              "passing_score": 60, "max_attempts": 3}
QUESTIONS = [
    {"text": "¿Qué patrón desacopla al publicador de sus suscriptores?",
     "options": ["Singleton", "Observer", "Builder"], "correct_option": 1, "points": 5},
    {"text": "¿Qué patrón agrega operaciones a un Composite sin modificarlo?",
     "options": ["Visitor", "Adapter", "Proxy"], "correct_option": 0, "points": 5},
]
API_ASSESSMENT = {"title": "Examen de APIs", "description": "Rutas, dependencias y JWT",
                  "passing_score": 70, "max_attempts": 2}
API_QUESTIONS = [
    {"text": "¿Qué valida el cuerpo de una petición en FastAPI?",
     "options": ["Pydantic", "Jinja", "SQLite"], "correct_option": 0, "points": 4},
    {"text": "¿Qué código HTTP indica un recurso creado?",
     "options": ["200", "201", "204"], "correct_option": 1, "points": 3},
    {"text": "¿Dónde viaja normalmente un JWT?",
     "options": ["En la URL", "En el header Authorization", "En una cookie de terceros"],
     "correct_option": 1, "points": 3},
]
DATA_ASSESSMENT = {"title": "Evaluación de pandas", "description": "Conceptos básicos",
                   "passing_score": 60, "max_attempts": 2}
DATA_QUESTIONS = [
    {"text": "¿Qué estructura de pandas representa una tabla?",
     "options": ["Series", "DataFrame", "ndarray"], "correct_option": 1, "points": 5},
    {"text": "¿Qué método muestra las primeras filas?",
     "options": ["head()", "top()", "first()"], "correct_option": 0, "points": 5},
]
# Queda en BORRADOR a propósito: en la demo se publica en vivo (State).
ML_DRAFT_ASSESSMENT = {"title": "Quiz de modelos (borrador)",
                       "description": "Publícala en la demo para ver el patrón State",
                       "passing_score": 60, "max_attempts": 1}
ML_DRAFT_QUESTIONS = [
    {"text": "¿Qué modelo predice un valor continuo?",
     "options": ["Regresión lineal", "K-means", "Apriori"], "correct_option": 0, "points": 5},
]

# ---------------------------------------------------------- clases en vivo
LIVE_SESSION = {"title": "Clase en vivo: patrones en la práctica",
                "duration_minutes": 60}
# Queda PROGRAMADA a propósito: en la demo se inicia y termina (State).
ML_LIVE_SESSION = {"title": "Sesión en vivo: entrenando tu primer modelo",
                   "duration_minutes": 90}

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
    return {"token": body["access_token"], "user_id": body["user"]["user_id"],
            "email": user["email"]}


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


def _create_assessment(request, inst, course_id, spec, questions, *, publish=True):
    """Crea la evaluación y devuelve (id, respuestas_correctas, respuestas_incorrectas)."""
    a = _expect(request("POST", "/assessments", {**spec, "course_id": course_id},
                        inst["token"]), 201, what=f"crear evaluación {spec['title']}")
    aid = a["id"]
    for q in questions:
        _expect(request("POST", f"/assessments/{aid}/questions", q, inst["token"]),
                201, what="pregunta")
    if publish:
        _expect(request("POST", f"/assessments/{aid}/publish", None, inst["token"]),
                200, what=f"publicar {spec['title']}")
    full = _expect(request("GET", f"/assessments/{aid}", None, inst["token"]), 200,
                   what="leer evaluación")
    correct = {q["question_id"]: q["correct_option"] for q in full["questions"]}
    wrong = {q["question_id"]: (q["correct_option"] + 1) % len(q["options"])
             for q in full["questions"]}
    return aid, correct, wrong


def _lesson_ids(request, student, course_id) -> List[str]:
    summary = _expect(request("GET", f"/courses/{course_id}/content/summary", None,
                              student["token"]), 200, what="resumen")
    return [lesson["lesson_id"]
            for module in summary["syllabus"] for lesson in module["lessons"]]


def _complete_lessons(request, student, course_id, count=None) -> int:
    ids = _lesson_ids(request, student, course_id)
    ids = ids if count is None else ids[:count]
    for lid in ids:
        _expect(request("POST", f"/courses/{course_id}/lessons/{lid}/complete", None,
                        student["token"]), 200, what="completar lección")
    return len(ids)


def _enroll_free(request, student, course_id):
    _expect(request("POST", f"/courses/{course_id}/enroll", None, student["token"]),
            200, 409, what="inscripción gratuita")


def _course_price(request, course_id) -> float:
    """Precio final publicado (ya incluye el recargo premium del Decorator)."""
    courses = _expect(request("GET", "/courses/", None, None), 200, what="listar cursos")
    return next(c["price"] for c in courses if c["id"] == course_id)


def _pay(request, student, course_id, gateway):
    """Pago aprobado -> el Observer inscribe automáticamente al estudiante."""
    amount = _course_price(request, course_id)
    _expect(request("POST", "/payments/process", {
        "amount": amount, "currency": "USD", "gateway": gateway, "course_id": course_id,
    }, student["token"]), 200, 409, what=f"pago {gateway} de {student['email']}")


def _attempt(request, student, assessment_id, answers) -> dict:
    return _expect(request("POST", f"/assessments/{assessment_id}/attempts",
                           {"answers": answers}, student["token"]), 201,
                   what=f"intento de {student['email']}")


def _tomorrow_iso() -> str:
    when = datetime.now(timezone.utc) + timedelta(days=1)
    return when.replace(hour=15, minute=0, second=0, microsecond=0).isoformat()


def run_seed(request: Requester, *, create_admin: Callable[[], bool] = ensure_admin,
             log: Callable[[str], None] = print) -> dict:
    admin_created = create_admin()
    log(("+ " if admin_created else "= ") + f"admin {ADMIN['email']}")
    inst = _login(request, INSTRUCTOR)
    laura = _login(request, INSTRUCTOR_2)
    alum = _login(request, STUDENT)
    carlos = _login(request, CARLOS)
    valentina = _login(request, VALENTINA)
    lucia = _login(request, LUCIA)
    mateo = _login(request, MATEO)
    log(f"= instructores: {INSTRUCTOR['email']}, {INSTRUCTOR_2['email']}")
    log("= estudiantes: " + ", ".join(
        u["email"] for u in (STUDENT, CARLOS, VALENTINA, LUCIA, MATEO)))

    free_id, free_new = _ensure_course(request, inst, FREE_COURSE, FREE_LESSONS, log)
    premium_id, premium_new = _ensure_course(
        request, inst, PREMIUM_COURSE, PREMIUM_LESSONS, log)
    api_id, api_new = _ensure_course(request, inst, API_COURSE, API_LESSONS, log)
    data_id, data_new = _ensure_course(request, laura, DATA_COURSE, DATA_LESSONS, log)
    ml_id, ml_new = _ensure_course(request, laura, ML_COURSE, ML_LESSONS, log)
    sql_id, sql_new = _ensure_course(request, laura, SQL_COURSE, SQL_LESSONS, log)

    # Sofía: inscrita en el gratuito con una lección completada (idempotente).
    _enroll_free(request, alum, free_id)
    _complete_lessons(request, alum, free_id, count=1)

    assessment_id = None
    session_id = None
    certificates: Dict[str, int] = {}

    # --- Arquitectura (premium): evaluación, clase grabada y 2 certificados.
    if premium_new:
        assessment_id, correct, _ = _create_assessment(
            request, inst, premium_id, ASSESSMENT, QUESTIONS)
        log(f"+ evaluación publicada: {ASSESSMENT['title']} ({assessment_id})")

        s = _expect(request("POST", "/live-sessions", {**LIVE_SESSION, "course_id": premium_id},
                            inst["token"]), 201, what="programar clase")
        session_id = s["id"]
        _expect(request("POST", f"/live-sessions/{session_id}/start", None, inst["token"]),
                200, what="iniciar clase")
        ended = _expect(request("POST", f"/live-sessions/{session_id}/end", None,
                                inst["token"]), 200, what="terminar clase")
        log(f"+ clase grabada: {ended['recording_url']}")

        for student, gateway in ((carlos, "stripe"), (valentina, "wompi")):
            _pay(request, student, premium_id, gateway)
            _complete_lessons(request, student, premium_id)
            result = _attempt(request, student, assessment_id, correct)
            log(f"+ {student['email']}: pagó con {gateway}, completó el curso y "
                f"sacó {result['percentage']}% -> certificado")

    # --- Diseño de APIs (premium): Lucía paga, avanza y reprueba.
    if api_new:
        api_assessment, _, wrong = _create_assessment(
            request, inst, api_id, API_ASSESSMENT, API_QUESTIONS)
        log(f"+ evaluación publicada: {API_ASSESSMENT['title']} ({api_assessment})")
        _pay(request, lucia, api_id, "wompi")
        _complete_lessons(request, lucia, api_id, count=2)
        result = _attempt(request, lucia, api_assessment, wrong)
        log(f"+ {lucia['email']}: reprobó el examen de APIs ({result['percentage']}%) "
            "-> recomendaciones de refuerzo")

    # --- Ciencia de Datos (gratis, con certificado): Valentina lo aprueba.
    if data_new:
        data_assessment, correct, _ = _create_assessment(
            request, laura, data_id, DATA_ASSESSMENT, DATA_QUESTIONS)
        log(f"+ evaluación publicada: {DATA_ASSESSMENT['title']} ({data_assessment})")
        _enroll_free(request, valentina, data_id)
        _complete_lessons(request, valentina, data_id)
        _attempt(request, valentina, data_assessment, correct)
        log(f"+ {valentina['email']}: segundo certificado (Ciencia de Datos)")

    # --- Machine Learning (en vivo): clase PROGRAMADA y evaluación en BORRADOR.
    ml_session_id = None
    ml_draft_id = None
    if ml_new:
        s = _expect(request("POST", "/live-sessions", {
            **ML_LIVE_SESSION, "course_id": ml_id, "scheduled_at": _tomorrow_iso(),
        }, laura["token"]), 201, what="programar clase de ML")
        ml_session_id = s["id"]
        log(f"+ clase programada para mañana: {ML_LIVE_SESSION['title']}")
        ml_draft_id, _, _ = _create_assessment(
            request, laura, ml_id, ML_DRAFT_ASSESSMENT, ML_DRAFT_QUESTIONS, publish=False)
        log(f"+ evaluación en borrador: {ML_DRAFT_ASSESSMENT['title']}")

    # --- SQL (gratis): más inscripciones para la regla "popular".
    if sql_new:
        _enroll_free(request, lucia, sql_id)
        _complete_lessons(request, lucia, sql_id, count=1)
        _enroll_free(request, carlos, sql_id)
        log("+ Lucía y Carlos inscritos en SQL")

    # Carlos también cursa Python (popularidad y afinidad).
    if free_new:
        _enroll_free(request, carlos, free_id)
        _complete_lessons(request, carlos, free_id, count=2)

    for student in (alum, carlos, valentina, lucia, mateo):
        certs = _expect(request("GET", "/certificates/me", None, student["token"]), 200,
                        what="certificados")
        certificates[student["email"]] = len(certs)

    result = {
        "password": DEMO_PASSWORD,
        "admin": ADMIN["email"],
        "instructor": INSTRUCTOR["email"],
        "instructor_2": INSTRUCTOR_2["email"],
        "student": STUDENT["email"],
        "students": [u["email"] for u in (STUDENT, CARLOS, VALENTINA, LUCIA, MATEO)],
        "free_course_id": free_id,
        "premium_course_id": premium_id,
        "course_ids": {
            "python": free_id, "arquitectura": premium_id, "apis": api_id,
            "datos": data_id, "ml": ml_id, "sql": sql_id,
        },
        "assessment_id": assessment_id,
        "live_session_id": session_id,
        "ml_live_session_id": ml_session_id,
        "ml_draft_assessment_id": ml_draft_id,
        "certificates": certificates,
    }
    log("Certificados: " + ", ".join(f"{k}={v}" for k, v in certificates.items()))
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

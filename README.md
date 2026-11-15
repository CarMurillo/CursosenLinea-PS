# CursosenLinea-PS: Plataforma de Cursos en Línea (LMS Avanzado)

LMS académico con backend **FastAPI + SQLAlchemy/SQLite** (`lms_backend/`) y frontend
**React 19 + Vite + react-router-dom 7 + axios** (`lms_frontend/`). El objetivo es demostrar
arquitectura hexagonal por módulos, 15 patrones GoF integrados en flujos reales, pruebas automatizadas,
CI y observabilidad mínima.

Funcionalidades:

- Cursos (video o clase en vivo, premium y/o con certificado), módulos y lecciones con duración.
- Pagos simulados (Stripe/Wompi) con inscripción automática al aprobarse.
- Contenido protegido para inscritos; progreso por estudiante.
- Evaluaciones con calificación automática y certificados verificables.
- Clases en vivo con grabación automática (Jitsi simulado).
- Recomendaciones por reglas, notificaciones in-app y log de auditoría.

Documentación detallada:

- [`docs/patrones.md`](docs/patrones.md): cada patrón → problema, clases, archivo, endpoint, prueba. Incluye la fe de erratas de la entrega anterior.
- [`docs/uml/`](docs/uml/): diagramas Mermaid (Observer, State, Visitor, secuencia pago → inscripción → certificado).
- [`docs/adr/`](docs/adr/): decisiones de arquitectura.

## Arquitectura

```
lms_backend/app/
├── main.py                     # FastAPI: CORS, middleware de logging, routers
├── shared/
│   ├── domain/                 # events.py (Observer), observers.py, state.py, errors.py
│   └── infrastructure/
│       ├── container.py        # COMPOSITION ROOT único: repositorios, bus de eventos, fábricas make_*
│       ├── config/system_config.py   # Singleton de configuración
│       ├── database.py, models.py, user_repository.py   # SQLite (usuarios)
│       ├── auth_deps.py        # get_current_user, require_role
│       └── observability.py    # GET /health y log de requests
├── modules/<modulo>/{domain,application,infrastructure}
│   auth, courses, payments, progress, assessments, live_sessions,
│   certificates, notifications, recommendations
└── users/                      # listado de usuarios (admin)
```

- **Hexagonal por módulos**: el dominio define puertos (`CourseRepository`, `PaymentGatewayPort`,
  `VideoConferencePort`, …); la infraestructura los implementa (repositorios en memoria, adaptadores
  simulados, routers FastAPI).
- **Composition root**: `app/shared/infrastructure/container.py` crea todas las instancias y el único bus
  de eventos. Los routers obtienen sus dependencias de ahí con `Depends`. Ver
  [ADR 0004](docs/adr/0004-composition-root-unico.md).

## Requisitos

- Python 3.10 o superior (CI usa 3.11).
- Node.js 22 (o 20.19+; Vite 8 lo exige) y npm.
- Git Bash o WSL solo si se quiere usar `run.sh` en Windows.

## Ejecución

### Backend (Windows PowerShell)

```powershell
cd lms_backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Backend (Linux/macOS)

```bash
cd lms_backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API en `http://127.0.0.1:8000`, Swagger en `http://127.0.0.1:8000/docs`.

### Frontend (igual en PowerShell y Linux)

```bash
cd lms_frontend
npm install
npm run dev
```

App en `http://localhost:5173`. El backend debe estar corriendo.

### `run.sh` (Linux, macOS o Git Bash/WSL en Windows)

```bash
./run.sh setup      # crea venv, instala dependencias de backend y frontend
./run.sh            # backend + frontend a la vez (Ctrl+C detiene ambos)
./run.sh backend    # solo backend (puerto PORT_API, por defecto 8000)
./run.sh frontend   # solo frontend
./run.sh test       # pytest del backend
```

## Variables de entorno

| Variable | Dónde | Por defecto | Uso |
|---|---|---|---|
| `DATABASE_URL` | backend (`SystemConfig`) | `sqlite:///./app.db` | BD de usuarios |
| `CORS_ORIGINS` | backend | `http://localhost:5173,http://127.0.0.1:5173` | orígenes permitidos, separados por coma (no `*`) |
| `LOG_LEVEL` | backend | `INFO` | nivel del logger `lms` |
| `APP_NAME` | backend | `LMS Advanced Platform` | nombre en Swagger y `/health` |
| `DEBUG_MODE` | backend | `True` | se lee en `SystemConfig`; hoy no cambia el comportamiento |
| `LMS_API_URL` | `scripts/seed.py` | `http://127.0.0.1:8000` | servidor contra el que corre el seed (también `--base-url`) |
| `VITE_API_URL` | frontend (`src/services/api.js`) | `http://127.0.0.1:8000` | URL base de la API |

## Datos de demostración (seed)

Con el backend corriendo, en otra terminal desde `lms_backend/`:

```powershell
.\venv\Scripts\python scripts\seed.py
```

```bash
./venv/bin/python scripts/seed.py      # Linux/macOS
```

Cuentas (contraseña común `Demo12345`):

| Correo | Rol |
|---|---|
| `admin@lms.demo` | admin |
| `instructor@lms.demo` | instructor |
| `estudiante@lms.demo` | student |

Crea el curso gratuito "Fundamentos de Python" (estudiante inscrito con 1 lección completada) y el curso
premium con certificado "Arquitectura de Software con Patrones" (evaluación publicada y clase en vivo ya
grabada). El estudiante **no** queda inscrito en el premium: en la demo paga, se inscribe
automáticamente, rinde la evaluación y obtiene el certificado.

El seed es idempotente. Los cursos, pagos, progreso y evaluaciones viven en memoria: **al reiniciar el
backend hay que volver a ejecutar el seed** (los usuarios persisten en SQLite) y volver a iniciar sesión.

## Observabilidad

- `GET /health` (público): `status`, `app`, `version`, `uptime_seconds`, estado de la BD y contadores
  (cursos, inscripciones, pagos, evaluaciones, clases, certificados, notificaciones, eventos de
  auditoría, observadores del bus).
- Cada request se registra con `logging` en el logger `lms.requests`:
  `method=… path=… status=… duration_ms=…`.

## Pruebas

```powershell
cd lms_backend
.\venv\Scripts\python -m pytest -q
```

```bash
cd lms_backend && ./venv/bin/python -m pytest -q
```

Las pruebas usan SQLite en memoria (`tests/conftest.py`) y nunca tocan `app.db`.
Frontend: `npm run lint` y `npm run build` en `lms_frontend/`.

CI (GitHub Actions, `.github/workflows/ci.yml`): job backend (Python 3.11, `pytest`) y job frontend
(Node 22, `npm ci`, lint, build).

## Docker (backend)

```bash
cd lms_backend
docker build -t lms-backend .
docker run --rm -p 8000:8000 -v lms-data:/data lms-backend
```

La imagen guarda los usuarios en `/data/app.db` (volumen). No se verificó en este equipo.

## Mapa de endpoints

Auth: `Authorization: Bearer <access_token>` (de `POST /auth/login`). "Staff" = instructor o admin;
"dueño" = instructor creador del curso.

| Método | Ruta | Acceso | Patrones |
|---|---|---|---|
| GET | `/` | público | |
| GET | `/health` | público | Singleton |
| POST | `/auth/register` | público (student/instructor) | Abstract Factory |
| POST | `/auth/login` | público | |
| GET | `/users/` | admin | |
| GET | `/courses/` | público | Facade |
| POST | `/courses/` | staff | Facade, Builder, Factory Method, Decorator, Observer |
| GET | `/courses/me/enrolled` | token | Facade |
| GET | `/courses/content-metadata/{content_type}` | público | Flyweight |
| POST | `/courses/{course_id}/clone` | dueño/admin | Prototype |
| POST | `/courses/{course_id}/enroll` | token (pago aprobado si es de pago) | Facade, Observer |
| POST | `/courses/{course_id}/content/lessons` | dueño/admin | Bridge, Composite |
| GET | `/courses/{course_id}/content` | token; inscrito si es de pago | Proxy, Composite |
| GET | `/courses/{course_id}/content/summary` | igual que `/content` | Visitor, Proxy |
| POST | `/courses/{course_id}/lessons/{lesson_id}/complete` | inscrito/dueño/admin | Visitor, Proxy, Observer |
| GET | `/courses/{course_id}/progress/me` | inscrito/dueño/admin | Visitor, Proxy |
| GET | `/courses/{course_id}/assessments` | inscrito/dueño/admin | State |
| GET | `/courses/{course_id}/live-sessions` | inscrito/dueño/admin | State |
| POST | `/payments/process` | token | Adapter, Observer |
| GET | `/payments/me` | token | |
| GET | `/notifications/me` | token | Observer |
| GET | `/admin/audit-log` | admin | Observer |
| POST | `/assessments` | staff (dueño del curso) | State |
| POST | `/assessments/{assessment_id}/questions` | dueño/admin | State |
| POST | `/assessments/{assessment_id}/publish` | dueño/admin | State |
| POST | `/assessments/{assessment_id}/close` | dueño/admin | State |
| POST | `/assessments/{assessment_id}/attempts` | estudiante inscrito | State, Observer |
| GET | `/assessments/{assessment_id}` | token | State |
| POST | `/live-sessions` | staff (dueño del curso) | State |
| POST | `/live-sessions/{session_id}/start` | dueño/admin | State, Adapter |
| POST | `/live-sessions/{session_id}/end` | dueño/admin | State, Adapter, Observer |
| GET | `/live-sessions/{session_id}` | inscrito/dueño/admin | |
| GET | `/certificates/me` | token | |
| GET | `/certificates/verify/{code}` | público | |
| GET | `/recommendations/me` | token | Strategy, Visitor |

Códigos de error: 401 sin token o sesión inválida; 403 rol o acceso; 404 no existe; 409 duplicado o
transición de estado inválida; 400 pago rechazado o monto bajo; 422 validación.

## Limitaciones conocidas

- **Persistencia en memoria**: cursos, pagos, progreso, evaluaciones, clases en vivo, certificados,
  notificaciones, auditoría y perfiles de recomendación se pierden al reiniciar el backend. Solo los
  usuarios están en SQLite. Ver [ADR 0005](docs/adr/0005-repositorios-en-memoria-y-persistencia-minima.md).
- **Tokens**: opacos, guardados en memoria y sin expiración. Al reiniciar el backend todas las sesiones
  se invalidan (el frontend cierra sesión ante el 401).
- **Pagos simulados**: Stripe y Wompi son SDK falsos, sin red ni claves. El monto se compara contra el
  `price` del curso **sin conversión de moneda** (un pago en COP por Wompi y uno en USD por Stripe se
  validan contra el mismo número).
- **Videoconferencia simulada**: `JitsiAdapter` genera URLs; la URL de grabación no apunta a un archivo real.
- **Notificación de grabación**: solo la reciben el instructor y los estudiantes inscritos en el momento
  de terminar la clase; quien se inscribe después no recibe el aviso.
- **Acoplamiento en auth**: la capa de aplicación `lms_backend/app/modules/auth/application/use_cases.py`
  importa `infrastructure.security` (hash y emisión de tokens) en lugar de puertos inyectados. El dominio
  sí está libre de FastAPI/SQLAlchemy.
- **Sesiones**: los usuarios inactivos (`is_active=False`) reciben 401, pero los tokens no caducan ni hay logout.
- **Notificaciones leídas**: el backend no tiene "marcar como leída" (el campo `read` siempre es `false`).
  La campana del frontend guarda lo visto en `localStorage`, por navegador.
- **Bus de eventos síncrono**: los observadores corren dentro de la petición HTTP; no hay cola, reintentos
  ni persistencia de eventos. Ver [ADR 0001](docs/adr/0001-bus-de-eventos-sincrono-en-memoria.md).
- **Flyweight**: sin pruebas de carga ni medición de memoria.
- **Docker**: el `Dockerfile` del backend no se verificó en este equipo; no hay imagen del frontend.

## Autores

Carlos David Murillo Moreno · Juan David Villalobos Méndez

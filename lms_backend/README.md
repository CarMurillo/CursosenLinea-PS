# lms_backend: API del LMS (FastAPI)

Carlos David Murillo Moreno
Juan David Villalobos Méndez

API REST del LMS con arquitectura hexagonal por módulos
(`app/modules/<modulo>/{domain,application,infrastructure}`) y un composition root único
(`app/shared/infrastructure/container.py`). La visión general, el mapa de endpoints y las limitaciones
están en el [`README.md` raíz](../README.md); los patrones en [`docs/patrones.md`](../docs/patrones.md).

## Ejecutar

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1          # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Swagger: `http://127.0.0.1:8000/docs`. Salud: `GET /health`.

## Datos de demostración

Con el servidor arriba: `python scripts/seed.py` (opcional `--base-url`, o variable `LMS_API_URL`).
Cuentas `admin@lms.demo`, `instructor@lms.demo`, `estudiante@lms.demo`, contraseña `Demo12345`.
Repetir tras cada reinicio del servidor: solo los usuarios persisten (SQLite); el resto vive en memoria.

## Pruebas

```powershell
python -m pytest -q
```

Usan SQLite en memoria (`tests/conftest.py`) y `container.reset_state()` entre pruebas.

## Configuración

`SystemConfig` (Singleton) lee `DATABASE_URL` (por defecto `sqlite:///./app.db`), `CORS_ORIGINS`,
`LOG_LEVEL`, `APP_NAME` y `DEBUG_MODE`.

## Docker

```bash
docker build -t lms-backend .
docker run --rm -p 8000:8000 -v lms-data:/data lms-backend
```

No verificado en el equipo de desarrollo.

## Observabilidad

Logging estándar de Python (`logging`): una línea por request en el logger `lms.requests`
(`method`, `path`, `status`, `duration_ms`) y `GET /health` con contadores en memoria. No hay
integración con ELK, Prometheus/Grafana ni Datadog, ni se mide la cobertura de pruebas.

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.assessments.infrastructure.api import (
    courses_router as course_assessments_router,
    router as assessments_router,
)
from app.modules.auth.infrastructure.api import router as auth_router
from app.modules.certificates.infrastructure.api import router as certificates_router
from app.modules.courses.infrastructure.api import router as courses_router
from app.modules.live_sessions.infrastructure.api import (
    courses_router as course_live_sessions_router,
    router as live_sessions_router,
)
from app.modules.notifications.infrastructure.api import (
    admin_router as admin_router,
    router as notifications_router,
)
from app.modules.payments.infrastructure.api import router as payments_router
from app.modules.recommendations.infrastructure.api import (
    router as recommendations_router,
)
from app.shared.infrastructure.config.system_config import SystemConfig
from app.shared.infrastructure.database import init_db
from app.shared.infrastructure.observability import (
    configure_logging,
    log_requests,
    router as health_router,
)
from app.users.infrastructure.api import router as users_router

# Instancia del Singleton
config = SystemConfig()
configure_logging(config.log_level)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Crear tablas al arrancar (no al importar el módulo), en la BD que
    # indica SystemConfig().database_url.
    init_db()
    yield


app = FastAPI(title=config.app_name, version=config.version, lifespan=lifespan)

# Logging de cada request: método, ruta, status y duración en ms.
app.middleware("http")(log_requests)

# CORS: orígenes explícitos desde SystemConfig (CORS_ORIGINS); "*" no es
# válido junto con allow_credentials=True.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Todos los routers. Las dependencias (repositorios, bus de eventos único,
# servicios) salen del composition root: app/shared/infrastructure/container.py.
# Dentro de cada router las rutas literales (/courses/me/...,
# /courses/content-metadata/...) se declaran antes de /{course_id}.
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(courses_router)
app.include_router(payments_router)
app.include_router(notifications_router)
app.include_router(admin_router)
# Patrón State: evaluaciones, clases en vivo y certificados. Las rutas
# /courses/{id}/assessments y /courses/{id}/live-sessions viven en sus
# módulos (no colisionan con las del router de cursos).
app.include_router(assessments_router)
app.include_router(course_assessments_router)
app.include_router(live_sessions_router)
app.include_router(course_live_sessions_router)
app.include_router(certificates_router)
# Progreso (Visitor): POST /courses/{id}/lessons/{lesson_id}/complete y
# GET /courses/{id}/progress/me están en el router de cursos.
app.include_router(recommendations_router)


@app.get("/", tags=["health"])
def root():
    return {"message": "API del LMS activa", "app": config.system_name}


# --- PRUEBA RÁPIDA SINGLETON ---
if __name__ == "__main__":
    c1 = SystemConfig()
    c2 = SystemConfig()
    print("\n--- PRUEBA PATRÓN SINGLETON ---")
    print(f"¿Son la misma instancia?: {c1 is c2}")
    print(f"Dirección Memoria 1: {id(c1)}")
    print(f"Dirección Memoria 2: {id(c2)}")
    print("--------------------------------\n")

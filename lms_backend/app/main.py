
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.auth.infrastructure.api import router as auth_router
from app.modules.courses.infrastructure.api import router as courses_router
from app.shared.infrastructure.config.system_config import SystemConfig
from app.shared.infrastructure.database import Base, engine
from app.users.infrastructure.api import router as users_router

# Crear tablas en SQLite si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LMS Advanced Platform")

# Instancia del Singleton
config = SystemConfig()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite peticiones desde cualquier origen local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(courses_router)


@app.get("/")
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
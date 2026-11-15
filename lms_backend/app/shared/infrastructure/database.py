from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.shared.infrastructure.config.system_config import SystemConfig

# SINGLETON: la URL de la BD la gobierna SystemConfig (variable de entorno
# DATABASE_URL, por defecto sqlite:///./app.db).
DATABASE_URL = SystemConfig().database_url

# connect_args solo es necesario para SQLite
_connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """Crea las tablas si no existen (se invoca en el arranque de la app)."""
    # Importa los modelos para registrarlos en Base.metadata.
    from app.shared.infrastructure import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


# Dependency para FastAPI (proporciona una sesión de BD por request)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

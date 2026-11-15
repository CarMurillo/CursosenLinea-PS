import os

# Debe fijarse ANTES de importar la app: SystemConfig (Singleton) lee
# DATABASE_URL al crearse y database.py construye el engine con ella.
# Así pytest nunca escribe en el ./app.db real.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.shared.infrastructure import container
from app.shared.infrastructure.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///:memory:"

# StaticPool: una sola conexión compartida, necesaria para que SQLite en
# memoria persista entre las distintas sesiones que abre cada request.
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """Cliente de pruebas con una BD SQLite en memoria, aislada de app.db."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _reset_shared_state():
    # Cursos, pagos, progreso, notificaciones, auditoría, stubs de certificados/perfil y el bus único
    # (se re-cablea con sus observadores por defecto: quita los que un test
    # haya adjuntado).
    container.reset_state()


@pytest.fixture(autouse=True)
def _reset_course_repository():
    """Evita que el estado en memoria de un test contamine el siguiente."""
    _reset_shared_state()
    yield
    _reset_shared_state()
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.modules.courses.infrastructure.repository import course_repository
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


@pytest.fixture(autouse=True)
def _reset_course_repository():
    """Evita que los cursos publicados en un test contaminen el siguiente."""
    course_repository._courses.clear()
    yield
    course_repository._courses.clear()
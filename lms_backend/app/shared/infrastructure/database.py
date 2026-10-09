from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Usamos SQLite guardado en un archivo local 'app.db'
DATABASE_URL = "sqlite:///./app.db"

# connect_args solo es necesario para SQLite
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency para FastAPI (proporciona una sesión de BD por request)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
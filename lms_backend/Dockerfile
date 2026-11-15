# Imagen mínima del backend del LMS (FastAPI + uvicorn).
#   docker build -t lms-backend .
#   docker run --rm -p 8000:8000 -v lms-data:/data lms-backend
# Los usuarios se guardan en SQLite (/data/app.db, volumen); cursos, pagos,
# evaluaciones y progreso viven en memoria y se pierden al reiniciar el
# contenedor: reconstruye la demo con `python scripts/seed.py` desde el host
# (o `docker exec <contenedor> python scripts/seed.py`).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////data/app.db \
    CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

RUN mkdir -p /data
VOLUME ["/data"]
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

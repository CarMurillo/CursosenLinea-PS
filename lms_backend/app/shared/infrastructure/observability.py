"""Observabilidad sin dependencias nuevas: logging de requests y /health.

- `configure_logging(level)`: handler de consola para el logger `lms` (solo
  si la raíz no tiene handlers, para no duplicar líneas).
- `log_requests`: middleware HTTP que registra método, ruta, status y
  duración en ms, y devuelve la duración en la cabecera `X-Process-Time-Ms`.
- `router`: `GET /health` con estado, app/versión (SystemConfig), hora,
  uptime, chequeo de BD y contadores básicos del composition root.
"""

import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.shared.infrastructure import container
from app.shared.infrastructure.config.system_config import SystemConfig
from app.shared.infrastructure.database import get_db

request_logger = logging.getLogger("lms.requests")
_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level: str = "INFO") -> None:
    lms_logger = logging.getLogger("lms")
    lms_logger.setLevel(getattr(logging, level, logging.INFO))
    if not lms_logger.handlers and not logging.getLogger().handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMAT))
        lms_logger.addHandler(handler)


def _log(request: Request, status: int, start: float) -> float:
    elapsed_ms = (time.perf_counter() - start) * 1000
    request_logger.info(
        "method=%s path=%s status=%d duration_ms=%.2f",
        request.method,
        request.url.path,
        status,
        elapsed_ms,
    )
    return elapsed_ms


async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        _log(request, 500, start)   # error no controlado: se registra y sigue
        raise
    elapsed_ms = _log(request, response.status_code, start)
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
    return response


router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """Estado del servicio (público, sin token)."""
    config = SystemConfig()
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # noqa: BLE001 - se reporta, no se propaga
        logging.getLogger("lms.health").exception("Fallo el chequeo de BD")
        database = "error"

    now = datetime.now(timezone.utc)
    started = config.initialization_time
    return {
        "status": "ok" if database == "ok" else "degraded",
        "app": config.app_name,
        "version": config.version,
        "time": now.isoformat(),
        "started_at": started.isoformat(),
        "uptime_seconds": round((datetime.now() - started).total_seconds(), 2),
        "database": database,
        "counters": container.stats(),
    }

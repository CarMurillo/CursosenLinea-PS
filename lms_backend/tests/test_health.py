"""Observabilidad: GET /health, middleware de logging, CORS y openapi."""

import logging
from collections import Counter

from app.main import app
from app.shared.infrastructure.config.system_config import SystemConfig


def test_health_publico_con_version_y_contadores(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    config = SystemConfig()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["app"] == config.app_name
    assert body["version"] == config.version
    assert body["time"].endswith("+00:00")
    assert body["uptime_seconds"] >= 0
    counters = body["counters"]
    assert counters["courses"] == 0 and counters["payments"] == 0
    assert counters["event_observers"] >= 6       # bus único cableado


def test_health_contadores_reflejan_el_estado(client):
    client.post("/auth/register", json={"first_name": "I", "last_name": "N",
        "email": "i@x.com", "password": "Secreta123", "role": "instructor"})
    token = client.post("/auth/login", json={"email": "i@x.com",
        "password": "Secreta123"}).json()["access_token"]
    client.post("/courses/", json={"title": "Py", "price": 0, "course_type": "video"},
                headers={"Authorization": f"Bearer {token}"})
    counters = client.get("/health").json()["counters"]
    assert counters["courses"] == 1
    assert counters["audit_events"] >= 1          # COURSE_PUBLISHED auditado


def test_middleware_registra_metodo_ruta_status_y_ms(client, caplog):
    with caplog.at_level(logging.INFO, logger="lms.requests"):
        r = client.get("/courses/no-existe/content")
    assert r.status_code == 401
    assert float(r.headers["X-Process-Time-Ms"]) >= 0
    lines = [rec.getMessage() for rec in caplog.records if rec.name == "lms.requests"]
    assert any(
        "method=GET" in m and "path=/courses/no-existe/content" in m
        and "status=401" in m and "duration_ms=" in m
        for m in lines
    ), lines


def test_cors_permite_frontend_local_sin_comodin(client):
    assert "*" not in SystemConfig().cors_origins
    for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        r = client.options("/health", headers={
            "Origin": origin, "Access-Control-Request-Method": "GET"})
        assert r.headers.get("access-control-allow-origin") == origin
        assert r.headers.get("access-control-allow-credentials") == "true"
    r = client.options("/health", headers={
        "Origin": "http://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in r.headers


def _flat_routes(routes, prefix=""):
    """(métodos, ruta) en orden de resolución. Soporta routers incluidos
    tanto aplanados (FastAPI clásico) como anidados (`_IncludedRouter`)."""
    for route in routes:
        if getattr(route, "path", None) is not None:
            yield frozenset(getattr(route, "methods", None) or ()), prefix + route.path
        elif hasattr(route, "original_router"):
            sub_prefix = prefix + route.include_context.prefix
            yield from _flat_routes(route.original_router.routes, sub_prefix)


def test_openapi_monta_todos_los_routers_sin_rutas_duplicadas(client):
    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    for expected in ["/health", "/auth/login", "/users/", "/courses/", "/payments/process",
                     "/notifications/me", "/admin/audit-log", "/assessments",
                     "/certificates/me", "/live-sessions",
                     "/courses/{course_id}/lessons/{lesson_id}/complete",
                     "/courses/{course_id}/progress/me", "/recommendations/me"]:
        assert expected in paths, expected

    flat = list(_flat_routes(app.routes))
    pairs = Counter((method, path) for methods, path in flat for method in methods)
    assert [p for p, n in pairs.items() if n > 1] == []

    # Rutas literales /courses/... antes que la paramétrica /courses/{course_id}...
    order = [path for _, path in flat]
    first_param = min(i for i, p in enumerate(order) if p.startswith("/courses/{course_id}"))
    for literal in ("/courses/me/enrolled", "/courses/content-metadata/{content_type}"):
        assert order.index(literal) < first_param, literal

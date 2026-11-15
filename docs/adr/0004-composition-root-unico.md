# ADR 0004: Composition root único

- Estado: aceptado
- Código: `app/shared/infrastructure/container.py`, `app/main.py`

## Contexto

Antes había repositorios globales y buses creados en distintos módulos (por ejemplo, un `Subject` por
petición). Era fácil que dos routers usaran instancias diferentes del mismo repositorio y que los
observadores no recibieran los eventos.

## Decisión

- `container.py` crea **todas** las instancias compartidas: repositorios en memoria, `course_facade`,
  `JitsiAdapter`, `CertificateService` y el único `event_bus`, cableado por `wire_event_bus()`.
- Expone fábricas `make_*` que los routers usan con `Depends`.
- Dominio y aplicación reciben dependencias por constructor y no importan el contenedor. Solo la
  capa de infraestructura (routers) lo importa.
- `reset_state()` vacía los repositorios y re-cablea el mismo bus (lo usan las pruebas).
- `stats()` alimenta los contadores de `GET /health`.

## Consecuencias

- Positivas: un solo lugar para ver el grafo de dependencias y el mapa evento → observadores. Cambiar
  un adaptador (por ejemplo, un repositorio persistente) es un cambio local.
- Negativas: el módulo es grande y se importa al arrancar. Las instancias son globales del proceso,
  así que las pruebas deben llamar a `reset_state()` para aislarse.

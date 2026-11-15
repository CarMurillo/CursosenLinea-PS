# ADR 0005: Repositorios en memoria y persistencia mínima (B9)

- Estado: aceptado (deuda conocida)
- Código: `app/modules/*/infrastructure/repository.py`, `app/shared/infrastructure/database.py`,
  `app/shared/infrastructure/user_repository.py`, `app/modules/auth/infrastructure/security.py`

## Contexto

El proyecto es académico y el tiempo es limitado. Los usuarios ya estaban en SQLite con SQLAlchemy.
Cursos, pagos, progreso, evaluaciones, clases, certificados, notificaciones, auditoría y perfiles de
recomendación son agregados nuevos o recientes.

## Decisión

- Usuarios en SQLite (`DATABASE_URL`, por defecto `sqlite:///./app.db`) mediante `SqlAlchemyUserRepository`.
- El resto en repositorios `InMemory*` detrás de puertos de dominio (`CourseRepository`,
  `PaymentRepository`, `ProgressRepository`, etc.).
- Tokens opacos (`secrets.token_urlsafe`) en un diccionario en memoria, sin expiración.
- `scripts/seed.py` reconstruye la demo hablando con el servidor por HTTP, porque los datos en memoria
  viven dentro del proceso de uvicorn.
- El frontend cierra sesión ante un 401 (interceptor de axios).

## Consecuencias

- Positivas: arranque sin infraestructura externa; pruebas rápidas; los puertos permiten añadir
  adaptadores persistentes sin tocar dominio ni aplicación.
- Negativas: al reiniciar el backend se pierden cursos, pagos, progreso, evaluaciones, clases,
  certificados, notificaciones, auditoría y sesiones (los usuarios no). Hay que volver a ejecutar el
  seed e iniciar sesión otra vez. No sirve para varios procesos.
- Deuda: el puerto `app/users/domain/repositories.py` importa `UserModel` (SQLAlchemy). Eso viola la
  regla hexagonal de que el dominio no dependa de la infraestructura.

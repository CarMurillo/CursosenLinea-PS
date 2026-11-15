# ADR 0006: Autorización por rol y por propiedad (ownership)

- Estado: aceptado
- Código: `app/shared/infrastructure/auth_deps.py`, `app/modules/courses/infrastructure/api.py`,
  `app/shared/domain/state.py` (`CourseInfo.is_managed_by`), servicios de evaluaciones y clases en vivo

## Contexto

Crear cursos, clonar y agregar lecciones no exigían token. La inscripción recibía un `student_name`
libre y comparaba identidades por nombre, así que el acceso premium se podía saltar.

## Decisión

- Dependencias reutilizables: `get_current_user` (401 sin token o con token desconocido) y
  `require_role(...)` (403 si el rol no corresponde; `require_staff` = instructor o admin).
- Ownership: solo el instructor dueño del curso (`instructor_id`) o un admin pueden clonar, agregar
  lecciones y gestionar evaluaciones y clases en vivo.
- Identidad por el `user_id` del token. La inscripción en un curso premium o de pago exige un pago
  aprobado del mismo usuario para ese curso.
- El registro público no permite crear administradores (403). El admin de la demo lo crea el seed
  directamente en la BD.

## Consecuencias

- Positivas: reglas de acceso explícitas y probadas (`test_correcciones.py::test_b4_*`,
  `test_state.py::test_api_autorizacion_evaluaciones`, `::test_api_autorizacion_clases_en_vivo`).
- Negativas: la comprobación de ownership vive en cada módulo (no hay un servicio de autorización
  central). Los tokens no expiran.

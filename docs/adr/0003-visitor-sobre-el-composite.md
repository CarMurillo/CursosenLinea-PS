# ADR 0003: Visitor sobre el Composite de contenido

- Estado: aceptado
- Código: `app/modules/courses/domain/visitor.py`, `composite.py`, `content_component.py`, `bridge.py`,
  `content_proxy.py`

## Contexto

Se necesitan varias operaciones sobre el árbol de contenido: duración total, progreso por estudiante,
resumen por tipo, temario en markdown e índice de lecciones. Ponerlas en las clases del Composite las
haría crecer con cada requisito. Recorrer el árbol con `isinstance` en el cliente lo acopla a cada
tipo de nodo.

## Decisión

- `accept(visitor)` en `ContentComponent` y sus implementaciones: `LessonModule`, `CourseContent`,
  `VideoLesson`, `InteractiveQuizLesson` y `ProtectedContentProxy`.
- `ContentVisitor` con `visit_module`, `visit_lesson`, `visit_video_lesson`, `visit_quiz_lesson` y los
  ganchos `visit_course`, `leave_course`, `leave_module`.
- Visitantes concretos: `DurationVisitor`, `ProgressVisitor`, `ContentSummaryVisitor`,
  `ExportSyllabusVisitor`, `LessonIndexVisitor`.
- El Proxy valida el acceso antes de delegar: un visitante sin acceso no recorre nada.
- El progreso (lecciones completadas) es estado extrínseco en `ProgressRepository`, coherente con el
  Flyweight de metadatos.

## Consecuencias

- Positivas: una operación nueva es un visitante nuevo; el resumen, el progreso y las recomendaciones
  reutilizan los mismos visitantes; sin `isinstance` en el cliente
  (`test_visitor.py::test_doble_despacho_distingue_tipo_sin_isinstance`).
- Negativas: un tipo de nodo nuevo obliga a añadir su `visit_*` (mitigado: los métodos por tipo
  delegan por defecto en `visit_lesson`).

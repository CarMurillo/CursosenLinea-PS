# Visitor sobre el Composite de contenido

Fuente: `app/modules/courses/domain/visitor.py`, `content_component.py`, `composite.py`,
`bridge.py` y `content_proxy.py`.

```mermaid
classDiagram
    class ContentComponent {
        <<abstract>>
        +render_content() str
        +to_dict() dict
        +accept(visitor)*
    }
    class LessonModule {
        +title: str
        +add(component)
        +remove(component)
        +accept(visitor)
    }
    class CourseContent {
        +add_module(title)
        +find_module(title)
        +add_lesson(module_title, lesson)
        +accept(visitor)
    }
    class LessonContent {
        <<abstract>>
        +lesson_id: str
        +duration_minutes: int
        +metadata: ContentMetadata
    }
    class VideoLesson {
        +accept(visitor)
    }
    class InteractiveQuizLesson {
        +accept(visitor)
    }
    class ProtectedContentProxy {
        +accept(visitor)
    }

    class ContentVisitor {
        <<abstract>>
        +visit_module(module)*
        +visit_lesson(lesson)*
        +visit_video_lesson(lesson)
        +visit_quiz_lesson(lesson)
        +visit_course(content)
        +leave_course(content)
        +leave_module(module)
    }
    class DurationVisitor {
        +total_minutes
    }
    class ProgressVisitor {
        +ProgressVisitor(completed_lesson_ids)
        +percentage
    }
    class ContentSummaryVisitor {
        +result() dict
    }
    class ExportSyllabusVisitor {
        +to_markdown() str
    }
    class LessonIndexVisitor

    ContentComponent <|-- LessonModule
    LessonModule <|-- CourseContent
    ContentComponent <|-- LessonContent
    LessonContent <|-- VideoLesson
    LessonContent <|-- InteractiveQuizLesson
    ContentComponent <|-- ProtectedContentProxy
    LessonModule o--> "0..*" ContentComponent : hijos
    ProtectedContentProxy --> ContentComponent : sujeto real (perezoso)

    ContentVisitor <|-- DurationVisitor
    ContentVisitor <|-- ProgressVisitor
    ContentVisitor <|-- ContentSummaryVisitor
    ContentVisitor <|-- ExportSyllabusVisitor
    ContentVisitor <|-- LessonIndexVisitor
    ContentComponent ..> ContentVisitor : accept
```

## Doble despacho

| Nodo | `accept(visitor)` llama a |
|---|---|
| `CourseContent` | `visit_course`, hijos, `leave_course` (la raíz no cuenta como módulo) |
| `LessonModule` | `visit_module`, hijos, `leave_module` |
| `VideoLesson` | `visit_video_lesson` (por defecto delega en `visit_lesson`) |
| `InteractiveQuizLesson` | `visit_quiz_lesson` (por defecto delega en `visit_lesson`) |
| `ProtectedContentProxy` | valida el acceso; si no hay, lanza `ContentAccessDenied` (403); si hay, delega en el sujeto real |

## Dónde se usa

- `GET /courses/{course_id}/content/summary`: `ContentSummaryVisitor` + `ExportSyllabusVisitor` a través del Proxy.
- `POST /courses/{course_id}/lessons/{lesson_id}/complete` y `GET /courses/{course_id}/progress/me`:
  `CompleteLessonUseCase` / `GetProgressUseCase` recorren el Proxy de progreso.
- Recomendaciones: `VisitorProgressReader` (composition root) aplica `ProgressVisitor`.

# State: evaluaciones y clases en vivo

Fuente: `app/modules/assessments/domain/{models,states}.py`,
`app/modules/live_sessions/domain/{models,states}.py`, `app/shared/domain/state.py`.
Una operación no permitida en el estado actual lanza `InvalidStateTransition`, que la API
traduce a **409**.

## Evaluaciones: diagrama de estados

```mermaid
stateDiagram-v2
    [*] --> draft : POST /assessments
    draft --> draft : add_question
    draft --> published : publish [≥ 1 pregunta]
    published --> published : submit_attempt (calificación automática)
    published --> closed : close
    closed --> [*]

    note right of draft
        submit_attempt y close: 409
        publish sin preguntas: 409
    end note
    note right of published
        add_question y publish: 409
        intentos > max_attempts: 409
    end note
    note right of closed
        toda operación: 409
        resultados consultables
    end note
```

## Evaluaciones: diagrama de clases

```mermaid
classDiagram
    class Assessment {
        +assessment_id: str
        +course_id: str
        +passing_score: float
        +max_attempts: int
        +questions: list~Question~
        +attempts: list~Attempt~
        -_state: AssessmentState
        +state_name: str
        +add_question(question)
        +publish()
        +submit_attempt(user_id, answers) Attempt
        +close()
        ~_transition_to(state)
        ~_append_question(question)
        ~_grade_and_record(user_id, answers) Attempt
    }
    class AssessmentState {
        <<abstract>>
        +name: str
        +visible_to_students: bool
        +add_question(assessment, question)*
        +publish(assessment)*
        +submit_attempt(assessment, user_id, answers)*
        +close(assessment)*
    }
    class DraftState
    class PublishedState
    class ClosedState
    class InvalidStateTransition {
        +entity: str
        +state: str
        +action: str
    }
    class AssessmentService {
        +create(...)
        +add_question(...)
        +publish(...)
        +close(...)
        +submit_attempt(...)
    }

    Assessment o--> AssessmentState : delega
    AssessmentState <|-- DraftState
    AssessmentState <|-- PublishedState
    AssessmentState <|-- ClosedState
    AssessmentState ..> InvalidStateTransition : lanza
    AssessmentService --> Assessment
    AssessmentService ..> DomainEvent : ASSESSMENT_SUBMITTED, ASSESSMENT_GRADED
```

## Clases en vivo: diagrama de estados

```mermaid
stateDiagram-v2
    [*] --> scheduled : POST /live-sessions
    scheduled --> live : start (start_meeting)
    live --> ended : end (end_meeting)
    ended --> recorded : record (get_recording_url)
    recorded --> [*]

    note right of ended
        Transitorio: POST /live-sessions/{id}/end
        ejecuta end y record seguidos y publica
        LIVE_SESSION_RECORDED.
    end note
```

## Clases en vivo: diagrama de clases

```mermaid
classDiagram
    class LiveSession {
        +session_id: str
        +room_name: str
        +room_url: str
        +recording_url: str
        -_state: LiveSessionState
        +state_name: str
        +start(conference)
        +end(conference)
        +record(conference)
    }
    class LiveSessionState {
        <<abstract>>
        +name: str
        +start(session, conference)*
        +end(session, conference)*
        +record(session, conference)*
    }
    class ScheduledState
    class LiveState
    class EndedState
    class RecordedState
    class VideoConferencePort {
        <<Protocol>>
        +create_room(session_id, title)
        +start_meeting(room_name)
        +end_meeting(room_name)
        +get_recording_url(room_name)
    }
    class JitsiAdapter {
        <<simulado>>
        +provider_name = "jitsi"
    }
    class LiveSessionService {
        +schedule(...)
        +start(session_id, user_id, role)
        +end(session_id, user_id, role)
    }

    LiveSession o--> LiveSessionState : delega
    LiveSessionState <|-- ScheduledState
    LiveSessionState <|-- LiveState
    LiveSessionState <|-- EndedState
    LiveSessionState <|-- RecordedState
    LiveSessionState ..> VideoConferencePort : usa
    VideoConferencePort <|.. JitsiAdapter
    LiveSessionService --> LiveSession
    LiveSessionService --> VideoConferencePort
```

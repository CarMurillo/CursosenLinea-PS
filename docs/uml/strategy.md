# Strategy en el motor de recomendaciones

Fuente: `app/modules/recommendations/domain/strategies.py` (estrategias y contexto),
`app/modules/recommendations/domain/models.py` (`LearnerProfile`, `CourseSnapshot`, `Recommendation`) y
`app/modules/recommendations/application/use_cases.py` (`GetRecommendationsUseCase`).

```mermaid
classDiagram
    class RecommendationRule {
        <<abstract>>
        +name: str
        +weight: float
        +recommend(profile, candidates, catalog) List~Recommendation~*
        #_make(course, reason, bonus) Recommendation
    }
    class ReinforceAfterFailedAssessmentRule {
        +name = refuerzo
        +weight = 4.0
        +recommend(profile, candidates, catalog)
    }
    class NextLevelAfterCertificateRule {
        +name = siguiente_nivel
        +weight = 3.5
        +recommend(profile, candidates, catalog)
    }
    class SimilarToActiveCoursesRule {
        +name = afinidad
        +weight = 2.5
        +recommend(profile, candidates, catalog)
    }
    class FreeCoursesForNewcomersRule {
        +name = gratis_para_empezar
        +weight = 2.0
        +recommend(profile, candidates, catalog)
    }
    class PopularCoursesRule {
        +name = popular
        +weight = 1.5
        -_top: int
        +PopularCoursesRule(top=3)
        +recommend(profile, candidates, catalog)
    }
    class RecommendationEngine {
        -_rules: List~RecommendationRule~
        -_limit: int
        +RecommendationEngine(rules=None, limit=10)
        +recommend(profile, courses) List~dict~
    }
    class GetRecommendationsUseCase {
        +execute(user_id) List~dict~
    }
    class LearnerProfile
    class CourseSnapshot
    class Recommendation {
        +course_id: str
        +title: str
        +reason: str
        +rule: str
        +score: float
    }

    RecommendationRule <|-- ReinforceAfterFailedAssessmentRule
    RecommendationRule <|-- NextLevelAfterCertificateRule
    RecommendationRule <|-- SimilarToActiveCoursesRule
    RecommendationRule <|-- FreeCoursesForNewcomersRule
    RecommendationRule <|-- PopularCoursesRule
    RecommendationEngine o-- "1..*" RecommendationRule : rules (default_rules())
    GetRecommendationsUseCase --> RecommendationEngine : engine
    RecommendationRule ..> LearnerProfile : lee
    RecommendationRule ..> CourseSnapshot : candidates / catalog
    RecommendationRule ..> Recommendation : crea
```

Notas:

- `default_rules()` devuelve las cinco reglas concretas en el orden del diagrama. `RecommendationEngine`
  las usa cuando `rules` es `None`.
- El motor excluye los cursos inscritos y los propios antes de llamar a las reglas. Por curso conserva la
  recomendación de mayor `score` y acumula todos los motivos en `reasons`.
- `SimilarToActiveCoursesRule` usa `profile.progress`, que el caso de uso llena con el progreso calculado
  por `ProgressVisitor` (puerto `ProgressReaderPort`).
- Endpoint: `GET /recommendations/me`.

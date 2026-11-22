# ADR 0008: Strategy en el motor de recomendaciones

- Estado: aceptado (el código ya existía; esta entrega lo reconoce como patrón oficial)
- Código: `app/modules/recommendations/domain/strategies.py`,
  `app/modules/recommendations/application/use_cases.py`,
  `app/modules/recommendations/infrastructure/api.py`
- Pruebas: `tests/test_recommendations.py`

## Contexto

El motor de recomendaciones es un objetivo funcional del proyecto. Cada criterio es un algoritmo
distinto: refuerzo tras reprobar una evaluación, siguiente nivel tras un certificado, afinidad por
progreso, cursos gratis para estudiantes nuevos y cursos populares. La lista de criterios cambia y
crece. Un único método con un `if/elif` por regla mezclaría todos los criterios, y cada regla nueva
obligaría a modificarlo.

## Decisión

- Estrategia abstracta `RecommendationRule` (ABC) con `recommend(profile, candidates, catalog)`.
- Una clase por criterio: `ReinforceAfterFailedAssessmentRule`, `NextLevelAfterCertificateRule`,
  `SimilarToActiveCoursesRule`, `FreeCoursesForNewcomersRule` y `PopularCoursesRule`.
- `default_rules()` arma la lista por defecto.
- Contexto `RecommendationEngine(rules=None, limit=10)`: excluye inscritos y cursos propios, ejecuta
  las reglas, se queda con el mayor puntaje por curso y acumula los motivos.
- `GetRecommendationsUseCase` recibe el motor como dependencia opcional. El composition root usa el
  motor por defecto. Se expone en `GET /recommendations/me`.

## Consecuencias

- Positivas: agregar o quitar un criterio es una clase nueva o un cambio en la lista (OCP). Cada regla
  se prueba sola (SRP); `test_reglas_son_estrategias_intercambiables_y_hay_limite` inyecta una regla
  nueva sin tocar el motor. Cada recomendación es explicable (`rule`, `reason`, `reasons`).
- Negativas: los pesos (`weight`) y bonos están fijos en el código; no hay configuración por API ni
  aprendizaje. El orden final depende de esos pesos.

## Alternativas descartadas

- Un método con `if/elif` por regla: más corto al principio, pero rompe OCP y dificulta probar cada criterio.
- Un segundo Strategy para la política de calificación de evaluaciones: los requisitos solo piden una
  regla (porcentaje ≥ `passing_score`). Hoy no hay variación real; sería diseño especulativo (YAGNI).
  Si aparecen políticas como "mejor intento", "promedio" o "penalización", el punto de extensión es
  `Assessment._grade_and_record` (`app/modules/assessments/domain/models.py`).
- Tratar la selección de pasarela por diccionario (`default_gateways()` en
  `app/modules/payments/application/use_cases.py`) como un Strategy nuevo: es Adapter (ver ADR 0009).

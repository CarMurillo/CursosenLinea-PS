"""Motor de recomendaciones por reglas (Strategy) y GET /recommendations/me."""

import pytest

from app.modules.recommendations.application.use_cases import GetRecommendationsUseCase
from app.modules.recommendations.domain.models import (
    AssessmentResult,
    CourseSnapshot,
    LearnerProfile,
)
from app.modules.recommendations.domain.strategies import (
    FreeCoursesForNewcomersRule,
    NextLevelAfterCertificateRule,
    PopularCoursesRule,
    RecommendationEngine,
    RecommendationRule,
    ReinforceAfterFailedAssessmentRule,
    SimilarToActiveCoursesRule,
)
from app.modules.recommendations.infrastructure.repository import (
    InMemoryLearningProfileRepository,
)

PWD = "Secreta123"
VIDEO, LIVE = "Video bajo demanda", "Clase en Vivo (Videoconferencia)"


def _c(cid, instructor_id="i1", course_type=VIDEO, price=0.0, enrolled=0, premium=False):
    return CourseSnapshot(course_id=cid, title=cid.upper(), instructor=f"Prof {instructor_id}",
                          instructor_id=instructor_id, course_type=course_type,
                          price=price, premium=premium, enrolled_count=enrolled)


CATALOG = [
    _c("py", "i1", VIDEO, 0, enrolled=3),
    _c("py2", "i1", VIDEO, 50, enrolled=1),
    _c("js", "i2", VIDEO, 0),
    _c("live", "i3", LIVE, 20, enrolled=5),
    _c("mine", "u1", VIDEO, 0, enrolled=9),     # curso propio del usuario u1
]


def _ids(recs):
    return [r["course_id"] for r in recs]


# ------------------------------------------------------------------ dominio

def test_estudiante_nuevo_recibe_gratuitos_y_populares_con_motivo():
    recs = RecommendationEngine().recommend(LearnerProfile("u1"), CATALOG)
    by_id = {r["course_id"]: r for r in recs}
    assert "mine" not in by_id                       # nunca cursos propios
    assert by_id["py"]["rule"] == "gratis_para_empezar"
    assert by_id["js"]["rule"] == "gratis_para_empezar"
    assert "Gratis para empezar" in by_id["js"]["reason"]
    assert by_id["live"]["rule"] == "popular"
    assert "5 estudiante(s)" in by_id["live"]["reason"]
    # py además es popular: se conservan ambos motivos.
    assert len(by_id["py"]["reasons"]) == 2
    for r in recs:
        assert {"course_id", "title", "reason", "rule", "score"} <= set(r)


def test_excluye_cursos_inscritos():
    profile = LearnerProfile("u1", enrolled_course_ids=frozenset({"py", "live"}))
    assert {"py", "live", "mine"}.isdisjoint(_ids(RecommendationEngine().recommend(profile, CATALOG)))


def test_regla_afinidad_usa_progreso_del_visitor():
    profile = LearnerProfile("u9", enrolled_course_ids=frozenset({"py"}), progress={"py": 50.0})
    recs = SimilarToActiveCoursesRule().recommend(
        profile, [c for c in CATALOG if c.course_id != "py"], {c.course_id: c for c in CATALOG})
    by_id = {r.course_id: r for r in recs}
    assert "mismo instructor" in by_id["py2"].reason and "50%" in by_id["py2"].reason
    assert "mismo tipo" in by_id["js"].reason
    assert by_id["py2"].score > by_id["js"].score   # mismo instructor pesa más
    assert "live" not in by_id


def test_sin_progreso_no_aplica_afinidad():
    profile = LearnerProfile("u9", enrolled_course_ids=frozenset({"py"}), progress={"py": 0.0})
    assert SimilarToActiveCoursesRule().recommend(profile, CATALOG, {}) == []


def test_reprobado_recomienda_refuerzo_y_aprobado_lo_anula():
    catalog = {c.course_id: c for c in CATALOG}
    failed = LearnerProfile("u9", enrolled_course_ids=frozenset({"py"}), assessments=(
        AssessmentResult("py", "a1", 2, False),))
    recs = ReinforceAfterFailedAssessmentRule().recommend(failed, CATALOG[1:], catalog)
    assert recs and recs[0].course_id == "py2" and "Para reforzar" in recs[0].reason

    passed_later = LearnerProfile("u9", assessments=(
        AssessmentResult("py", "a1", 2, False), AssessmentResult("py", "a1", 10, True)))
    assert ReinforceAfterFailedAssessmentRule().recommend(passed_later, CATALOG, catalog) == []


def test_certificado_recomienda_siguiente_nivel_del_mismo_instructor():
    profile = LearnerProfile("u9", enrolled_course_ids=frozenset({"py"}),
                             certificate_course_ids=frozenset({"py"}))
    recs = RecommendationEngine().recommend(profile, CATALOG)
    assert recs[0]["course_id"] == "py2"
    assert recs[0]["rule"] == "siguiente_nivel"
    assert "certificado" in recs[0]["reason"]


def test_reglas_son_estrategias_intercambiables_y_hay_limite():
    class OnlyLive(RecommendationRule):
        name = "solo_vivo"

        def recommend(self, profile, candidates, catalog):
            return [self._make(c, "En vivo") for c in candidates if c.course_type == LIVE]

    recs = RecommendationEngine([OnlyLive()]).recommend(LearnerProfile("u1"), CATALOG)
    assert _ids(recs) == ["live"]
    assert len(RecommendationEngine(limit=1).recommend(LearnerProfile("u1"), CATALOG)) == 1
    assert PopularCoursesRule(top=1).recommend(LearnerProfile("x"), CATALOG, {})[0].course_id == "mine"
    assert FreeCoursesForNewcomersRule().recommend(
        LearnerProfile("x", enrolled_course_ids=frozenset({"py"})), CATALOG, {}) == []
    assert NextLevelAfterCertificateRule().recommend(LearnerProfile("x"), CATALOG, {}) == []


def test_caso_de_uso_combina_perfil_catalogo_y_progreso():
    profiles = InMemoryLearningProfileRepository()
    profiles.record_assessment("u9", "py", {"assessment_id": "a", "score": 1, "passed": False})

    class Catalog:
        def list_snapshots(self):
            return CATALOG

        def enrolled_course_ids(self, user_id):
            return ["py"]                       # inscripción real del catálogo

    class Progress:
        def progress_percent(self, user_id, course_id):
            return 40.0

    use_case = GetRecommendationsUseCase(profiles, Catalog(), Progress())
    profile = use_case.build_profile("u9")
    assert profile.enrolled_course_ids == {"py"}
    assert profile.progress == {"py": 40.0}
    assert profile.failed_course_ids() == ["py"]
    recs = use_case.execute("u9")
    assert recs[0]["rule"] == "refuerzo" and "py" not in _ids(recs)


# ------------------------------------------------------------------ endpoint

def _login(client, email, role):
    client.post("/auth/register", json={"first_name": "Ana", "last_name": email[0],
        "email": email, "password": PWD, "role": role})
    r = client.post("/auth/login", json={"email": email, "password": PWD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _course(client, headers, title, **extra):
    body = {"title": title, "price": 0, "course_type": "video", **extra}
    r = client.post("/courses/", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_endpoint_requiere_token(client):
    assert client.get("/recommendations/me").status_code == 401


def test_endpoint_nuevo_estudiante_y_luego_afinidad_por_progreso(client):
    inst = _login(client, "i@x.com", "instructor")
    other = _login(client, "o@x.com", "instructor")
    py = _course(client, inst, "Python")
    py2 = _course(client, inst, "Python avanzado", price=40)
    live = _course(client, other, "Taller en vivo", course_type="live", price=10)
    lesson = client.post(f"/courses/{py}/content/lessons", json={
        "module_title": "M", "title": "L", "media_id": "m", "provider": "vimeo",
        "duration_minutes": 5}, headers=inst).json()["lesson_id"]
    alum = _login(client, "a@x.com", "student")

    recs = client.get("/recommendations/me", headers=alum).json()
    assert [r["course_id"] for r in recs] == [py]           # solo el gratuito
    assert recs[0]["rule"] == "gratis_para_empezar"

    client.post(f"/courses/{py}/enroll", headers=alum)
    client.post(f"/courses/{py}/lessons/{lesson}/complete", headers=alum)
    recs = client.get("/recommendations/me", headers=alum).json()
    ids = [r["course_id"] for r in recs]
    assert py not in ids                                    # ya inscrito
    assert ids[0] == py2 and "100%" in recs[0]["reason"]
    assert live not in ids                                  # otro instructor y tipo, sin inscritos

    # El instructor nunca ve sus propios cursos.
    mine = client.get("/recommendations/me", headers=inst).json()
    assert {py, py2}.isdisjoint(r["course_id"] for r in mine)


@pytest.mark.parametrize("passed", [False, True])
def test_endpoint_tras_evaluacion(client, passed):
    inst = _login(client, "i@x.com", "instructor")
    base = _course(client, inst, "Base", certificate=True)
    nxt = _course(client, inst, "Siguiente", price=30)
    alum = _login(client, "a@x.com", "student")
    client.post(f"/courses/{base}/enroll", headers=alum)
    aid = client.post("/assessments", json={"course_id": base, "title": "Q",
                      "passing_score": 60}, headers=inst).json()["id"]
    qid = client.post(f"/assessments/{aid}/questions", json={"text": "?",
        "options": ["a", "b"], "correct_option": 1}, headers=inst).json()["question_id"]
    client.post(f"/assessments/{aid}/publish", headers=inst)
    r = client.post(f"/assessments/{aid}/attempts",
                    json={"answers": {qid: 1 if passed else 0}}, headers=alum)
    assert r.status_code == 201 and r.json()["passed"] is passed

    recs = client.get("/recommendations/me", headers=alum).json()
    assert recs[0]["course_id"] == nxt
    assert recs[0]["rule"] == ("siguiente_nivel" if passed else "refuerzo")

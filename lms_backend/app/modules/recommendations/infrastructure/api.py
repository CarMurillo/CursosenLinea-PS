"""Endpoint de recomendaciones personalizadas (motor por reglas)."""

from fastapi import APIRouter, Depends

from app.modules.recommendations.application.use_cases import GetRecommendationsUseCase
from app.shared.infrastructure import container
from app.shared.infrastructure.auth_deps import get_current_user

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommendations_use_case() -> GetRecommendationsUseCase:
    return container.make_recommendations_use_case()


@router.get("/me")
def my_recommendations(
    user=Depends(get_current_user),
    use_case: GetRecommendationsUseCase = Depends(get_recommendations_use_case),
):
    """Cursos sugeridos (no inscritos ni propios), cada uno con su `reason`."""
    return use_case.execute(user.id)

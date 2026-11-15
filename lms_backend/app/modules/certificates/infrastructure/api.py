"""Endpoints de certificados (la emisión la hace CertificateIssuerObserver)."""

from fastapi import APIRouter, Depends, HTTPException

from app.modules.certificates.application.services import CertificateService
from app.shared.infrastructure import container
from app.shared.infrastructure.auth_deps import get_current_user

router = APIRouter(prefix="/certificates", tags=["certificates"])


def get_certificate_service() -> CertificateService:
    return container.make_certificate_service()


@router.get("/me")
def my_certificates(
    user=Depends(get_current_user),
    service: CertificateService = Depends(get_certificate_service),
):
    return [c.to_dict() for c in service.list_by_user(user.id)]


@router.get("/verify/{code}")
def verify_certificate(
    code: str,
    service: CertificateService = Depends(get_certificate_service),
):
    """Verificación pública por código (no expone el user_id)."""
    certificate = service.verify(code)
    if certificate is None:
        raise HTTPException(status_code=404, detail="Certificado no encontrado")
    data = certificate.to_dict()
    data.pop("user_id", None)
    return {"valid": True, **data}

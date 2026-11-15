from fastapi import APIRouter, Depends, HTTPException

from app.modules.courses.infrastructure.repository import course_repository
from app.modules.payments.application.dtos import PaymentRequestDTO
from app.modules.payments.application.use_cases import (
    AlreadyPaidError,
    PaymentRejectedError,
    ProcessPaymentUseCase,
    UnsupportedGatewayError,
)
from app.modules.payments.infrastructure.repository import payment_repository
from app.shared.infrastructure.auth_deps import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])


def get_process_payment_use_case() -> ProcessPaymentUseCase:
    """Dependencia sobrescribible en pruebas (p. ej. pasarela que rechaza)."""
    return ProcessPaymentUseCase(payment_repository)


@router.post("/process")
def process_payment(
    dto: PaymentRequestDTO,
    user=Depends(get_current_user),
    use_case: ProcessPaymentUseCase = Depends(get_process_payment_use_case),
):
    if course_repository.get_by_id(dto.course_id) is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    try:
        payment = use_case.execute(dto, user_id=user.id, customer_email=user.email)
    except AlreadyPaidError:
        raise HTTPException(
            status_code=409, detail="Ya existe un pago aprobado para este curso."
        )
    except (PaymentRejectedError, UnsupportedGatewayError) as error:
        raise HTTPException(status_code=400, detail=str(error))

    return {
        "success": payment.is_approved,
        "payment_id": payment.payment_id,
        "status": payment.status.value,
        "course_id": payment.course_id,
        "transaction_id": payment.transaction_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "message": payment.message,
    }


@router.get("/me")
def my_payments(user=Depends(get_current_user)):
    """Historial de pagos del usuario autenticado."""
    return [p.to_dict() for p in payment_repository.list_by_user(user.id)]

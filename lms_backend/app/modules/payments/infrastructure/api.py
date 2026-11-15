from fastapi import APIRouter, Depends, HTTPException

from app.modules.payments.application.dtos import PaymentRequestDTO
from app.modules.payments.application.use_cases import (
    AlreadyEnrolledError,
    AlreadyPaidError,
    AmountBelowPriceError,
    PaymentNotAllowedError,
    PaymentRejectedError,
    ProcessPaymentUseCase,
    UnsupportedGatewayError,
)
from app.shared.infrastructure import container
from app.shared.infrastructure.auth_deps import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])


def get_process_payment_use_case() -> ProcessPaymentUseCase:
    """Dependencia sobrescribible en pruebas (p. ej. pasarela que rechaza).

    Usa el bus único (PAYMENT_APPROVED -> inscripción automática) y valida
    que el monto cubra el precio del curso."""
    return container.make_process_payment_use_case()


@router.post("/process")
def process_payment(
    dto: PaymentRequestDTO,
    user=Depends(get_current_user),
    use_case: ProcessPaymentUseCase = Depends(get_process_payment_use_case),
):
    if container.course_repository.get_by_id(dto.course_id) is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    try:
        payment = use_case.execute(
            dto,
            user_id=user.id,
            customer_email=user.email,
            customer_name=f"{user.first_name} {user.last_name}",
        )
    except AlreadyPaidError:
        raise HTTPException(
            status_code=409, detail="Ya existe un pago aprobado para este curso."
        )
    except AlreadyEnrolledError:
        raise HTTPException(
            status_code=409, detail="Ya estás inscrito en este curso."
        )
    except (
        PaymentRejectedError,
        UnsupportedGatewayError,
        AmountBelowPriceError,
        PaymentNotAllowedError,
    ) as error:
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
    return [p.to_dict() for p in container.payment_repository.list_by_user(user.id)]

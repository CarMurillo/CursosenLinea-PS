
from fastapi import APIRouter, HTTPException

from app.modules.payments.application.dtos import (
    PaymentRequestDTO
)

from app.modules.payments.application.use_cases import (
    ProcessPaymentUseCase
)


router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)


@router.post("/process")
def process_payment(dto: PaymentRequestDTO):

    try:

        result = ProcessPaymentUseCase().execute(dto)

        return {
            "success": result.success,
            "transaction_id": result.transaction_id,
            "amount": result.amount,
            "currency": result.currency,
            "message": result.message,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )



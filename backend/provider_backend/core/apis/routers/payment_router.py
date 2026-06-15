"""Mock-payment routes for the provider backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from commons.logger import logger
from core.controllers.payment_controller import PaymentController
from core.models.company_model import CompanyModel
from core.services.broker_auth_service import validate_broker_api_key
from core.apis.schemas.request_schema.payment_request_schema import (
    PaymentCreateRequest,
    PaymentOtpVerifyRequest,
)
from core.apis.schemas.response_schema.payment_response_schema import (
    PaymentCreateResponse,
    PaymentOtpSendResponse,
    PaymentOtpVerifyResponse,
    PaymentStatusResponse,
)

logging = logger(__name__)
router = APIRouter(prefix="/v1/payments", tags=["payments"])
payment_controller = PaymentController()


@router.post("", response_model=PaymentCreateResponse)
async def create_payment(
    payload: PaymentCreateRequest,
    broker_company: Annotated[CompanyModel, Depends(validate_broker_api_key)],
) -> PaymentCreateResponse:
    """Create a provider-side payment record for one transaction.

    Args:
        payload: Payment-creation payload.

    Returns:
        PaymentCreateResponse: Created payment response.

    Raises:
        HTTPException: If payment creation fails.
    """

    try:
        logging.info(
            "Calling /v1/payments endpoint for broker company %s",
            broker_company.company_name,
        )
        response = await payment_controller.create_payment(
            transaction_id=payload.transaction_id,
            user_id=payload.user_id,
            amount=payload.amount,
        )
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/payments endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/payments endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment.",
        )


@router.post("/{payment_reference}/send-otp", response_model=PaymentOtpSendResponse)
async def send_payment_otp(
    payment_reference: str,
    broker_company: Annotated[CompanyModel, Depends(validate_broker_api_key)],
) -> PaymentOtpSendResponse:
    """Generate and store a payment OTP for one payment reference.

    Args:
        payment_reference: Business payment reference of the current payment.

    Returns:
        PaymentOtpSendResponse: Payment-OTP generation response.

    Raises:
        HTTPException: If payment OTP generation fails.
    """

    try:
        logging.info(
            "Calling /v1/payments/%s/send-otp endpoint for broker company %s",
            payment_reference,
            broker_company.company_name,
        )
        response = await payment_controller.send_payment_otp(payment_reference)
        return response
    except HTTPException as httperror:
        logging.error(
            "Error in /v1/payments/%s/send-otp endpoint: %s",
            payment_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in /v1/payments/%s/send-otp endpoint: %s",
            payment_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send payment OTP.",
        )


@router.post("/verify-otp", response_model=PaymentOtpVerifyResponse)
async def verify_payment_otp(
    payload: PaymentOtpVerifyRequest,
    broker_company: Annotated[CompanyModel, Depends(validate_broker_api_key)],
) -> PaymentOtpVerifyResponse:
    """Verify a payment OTP and mark the payment successful.

    Args:
        payload: Payment-OTP verification payload.

    Returns:
        PaymentOtpVerifyResponse: Payment-OTP verification response.

    Raises:
        HTTPException: If payment OTP verification fails.
    """

    try:
        logging.info(
            "Calling /v1/payments/verify-otp endpoint for transaction %s and broker company %s",
            payload.transaction_id,
            broker_company.company_name,
        )
        response = await payment_controller.verify_payment_otp(
            transaction_id=payload.transaction_id,
            payment_reference=payload.payment_reference,
            otp=payload.otp,
        )
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/payments/verify-otp endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/payments/verify-otp endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify payment OTP.",
        )


@router.get("/{payment_reference}/status", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_reference: str,
    broker_company: Annotated[CompanyModel, Depends(validate_broker_api_key)],
) -> PaymentStatusResponse:
    """Return payment status details for one payment reference.

    Args:
        payment_reference: Business payment reference of the current payment.

    Returns:
        PaymentStatusResponse: Payment-status response.

    Raises:
        HTTPException: If payment status cannot be returned.
    """

    try:
        logging.info(
            "Calling /v1/payments/%s/status endpoint for broker company %s",
            payment_reference,
            broker_company.company_name,
        )
        response = await payment_controller.get_payment_status(payment_reference)
        return response
    except HTTPException as httperror:
        logging.error(
            "Error in /v1/payments/%s/status endpoint: %s",
            payment_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in /v1/payments/%s/status endpoint: %s",
            payment_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment status.",
        )

"""Payment routes for the InsureFlow main backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decodeJWT
from commons.logger import logger
from core.controllers.payment_controller import PaymentController
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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/login-otp/verify")
payment_router = APIRouter(tags=["payments"])


def _get_authenticated_user(token: str) -> dict:
    """Validate a JWT token and return its decoded payload."""

    authenticated_user_details = decodeJWT(token=token)
    if not authenticated_user_details:
        logging.warning("Invalid or expired token provided for main payment routes")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return authenticated_user_details


@payment_router.post(
    "/v1/payments",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    payload: PaymentCreateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> PaymentCreateResponse:
    """Create a payment session for one transaction."""

    try:
        logging.info("Calling POST /v1/payments endpoint")
        authenticated_user_details = _get_authenticated_user(token)
        if (
            authenticated_user_details.get("user_role") != "ADMIN"
            and authenticated_user_details.get("id") != payload.user_id
        ):
            logging.warning(
                "Unauthorized payment creation attempt for user ID %s by user ID %s",
                payload.user_id,
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create this payment.",
            )
        return await PaymentController().create_payment(payload)
    except HTTPException as httperror:
        logging.error("Error in POST /v1/payments endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in POST /v1/payments endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment",
        )


@payment_router.post(
    "/v1/payments/{payment_reference}/send-otp",
    response_model=PaymentOtpSendResponse,
    status_code=status.HTTP_200_OK,
)
async def send_payment_otp(
    payment_reference: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> PaymentOtpSendResponse:
    """Send a payment OTP for one payment reference."""

    try:
        logging.info("Calling POST /v1/payments/%s/send-otp endpoint", payment_reference)
        _get_authenticated_user(token)
        return await PaymentController().send_payment_otp(payment_reference)
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/payments/%s/send-otp endpoint: %s",
            payment_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/payments/%s/send-otp endpoint: %s",
            payment_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send payment OTP",
        )


@payment_router.post(
    "/v1/payments/verify-otp",
    response_model=PaymentOtpVerifyResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_payment_otp(
    payload: PaymentOtpVerifyRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> PaymentOtpVerifyResponse:
    """Verify a payment OTP and complete the purchase flow."""

    try:
        logging.info("Calling POST /v1/payments/verify-otp endpoint")
        _get_authenticated_user(token)
        return await PaymentController().verify_payment_otp(payload)
    except HTTPException as httperror:
        logging.error("Error in POST /v1/payments/verify-otp endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in POST /v1/payments/verify-otp endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify payment OTP",
        )


@payment_router.get(
    "/v1/payments/{payment_reference}/status",
    response_model=PaymentStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_payment_status(
    payment_reference: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> PaymentStatusResponse:
    """Fetch payment status details for one payment reference."""

    try:
        logging.info("Calling GET /v1/payments/%s/status endpoint", payment_reference)
        _get_authenticated_user(token)
        return await PaymentController().get_payment_status(payment_reference)
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/payments/%s/status endpoint: %s",
            payment_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/payments/%s/status endpoint: %s",
            payment_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment status",
        )

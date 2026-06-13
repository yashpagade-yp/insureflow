"""Provider-admin authentication routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ....commons.logger import logger
from ...controllers.auth_controller import ProviderAuthController
from ..schemas.request_schema.auth_request_schema import (
    ProviderAdminLoginRequest,
    ProviderAdminLoginVerifyRequest,
)
from ..schemas.response_schema.auth_response_schema import (
    ProviderAdminLoginOtpResponse,
    ProviderAdminLoginVerifyResponse,
)

logging = logger(__name__)
router = APIRouter(prefix="/v1/provider-auth", tags=["provider-auth"])
provider_auth_controller = ProviderAuthController()


@router.post("/login", response_model=ProviderAdminLoginOtpResponse)
async def start_provider_admin_login(
    payload: ProviderAdminLoginRequest,
) -> ProviderAdminLoginOtpResponse:
    """Start provider-admin login by validating password and generating OTP.

    Args:
        payload: Provider-admin login payload containing email and password.

    Returns:
        ProviderAdminLoginOtpResponse: OTP-generation response for provider-admin login.

    Raises:
        HTTPException: If the provider-admin login flow cannot be started.
    """

    try:
        logging.info("Calling /v1/provider-auth/login endpoint")
        response = await provider_auth_controller.start_login(payload)
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/provider-auth/login endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/provider-auth/login endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )


@router.post("/verify-otp", response_model=ProviderAdminLoginVerifyResponse)
async def verify_provider_admin_login(
    payload: ProviderAdminLoginVerifyRequest,
) -> ProviderAdminLoginVerifyResponse:
    """Verify provider-admin OTP and return an authenticated access token.

    Args:
        payload: Provider-admin OTP verification payload.

    Returns:
        ProviderAdminLoginVerifyResponse: Authenticated provider-admin token response.

    Raises:
        HTTPException: If provider-admin OTP verification fails.
    """

    try:
        logging.info("Calling /v1/provider-auth/verify-otp endpoint")
        response = await provider_auth_controller.verify_login(payload)
        return response
    except HTTPException as httperror:
        logging.error(
            "Error in /v1/provider-auth/verify-otp endpoint: %s",
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/provider-auth/verify-otp endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )

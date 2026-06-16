"""User routes for the InsureFlow main backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decodeJWT
from commons.logger import logger
from core.controllers.user_controller import UserController
from core.apis.schemas.request_schema.auth_request_schema import (
    AdminLoginRequest,
    AdminLoginVerifyRequest,
)
from core.apis.schemas.request_schema.user_request_schema import (
    AdminUpdateRequest,
    UserLoginOtpRequest,
    UserLoginVerifyRequest,
    UserUpdateRequest,
)
from core.apis.schemas.response_schema.auth_response_schema import (
    AdminLoginOtpResponse,
    AdminLoginVerifyResponse,
)
from core.apis.schemas.response_schema.user_response_schema import (
    AdminResponse,
    UserListResponse,
    UserLoginOtpResponse,
    UserLoginVerifyResponse,
    UserResponse,
)

logging = logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/login-otp/verify")
user_router = APIRouter(tags=["users"])


def _get_authenticated_user(token: str) -> dict:
    """Validate a JWT token and return its decoded payload."""

    authenticated_user_details = decodeJWT(token=token)
    if not authenticated_user_details:
        logging.warning("Invalid or expired token provided for main user routes")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return authenticated_user_details


@user_router.post(
    "/v1/users/login-otp",
    response_model=UserLoginOtpResponse,
    status_code=status.HTTP_200_OK,
)
async def send_login_otp(payload: UserLoginOtpRequest) -> UserLoginOtpResponse:
    """Send a login OTP to a customer's mobile number.

    Args:
        payload: Request containing the customer mobile number.

    Returns:
        OTP generation response with expiry details.

    Raises:
        HTTPException: If OTP generation fails.
    """

    try:
        logging.info("Calling /v1/users/login-otp endpoint")
        return await UserController().send_login_otp(payload)
    except HTTPException as httperror:
        logging.error("Error in /v1/users/login-otp endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/users/login-otp endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send login OTP",
        )


@user_router.post(
    "/v1/users/login-otp/verify",
    response_model=UserLoginVerifyResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_login_otp(
    payload: UserLoginVerifyRequest,
) -> UserLoginVerifyResponse:
    """Verify a customer's login OTP and return an access token.

    Args:
        payload: OTP verification payload for the customer.

    Returns:
        Authenticated user token response.

    Raises:
        HTTPException: If OTP verification fails.
    """

    try:
        logging.info("Calling /v1/users/login-otp/verify endpoint")
        return await UserController().verify_login_otp(payload)
    except HTTPException as httperror:
        logging.error("Error in /v1/users/login-otp/verify endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/users/login-otp/verify endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify login OTP",
        )


@user_router.post(
    "/v1/admins/login",
    response_model=AdminLoginOtpResponse,
    status_code=status.HTTP_200_OK,
)
async def send_admin_login_otp(
    payload: AdminLoginRequest,
) -> AdminLoginOtpResponse:
    """Validate admin credentials and send an admin login OTP.

    Args:
        payload: Admin login request containing email and password.

    Returns:
        Admin OTP generation response with expiry details.

    Raises:
        HTTPException: If credential validation or OTP generation fails.
    """

    try:
        logging.info("Calling /v1/admins/login endpoint")
        return await UserController().send_admin_login_otp(payload)
    except HTTPException as httperror:
        logging.error("Error in /v1/admins/login endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/admins/login endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send admin login OTP",
        )


@user_router.post(
    "/v1/admins/login/verify",
    response_model=AdminLoginVerifyResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_admin_login_otp(
    payload: AdminLoginVerifyRequest,
) -> AdminLoginVerifyResponse:
    """Verify an admin login OTP and return an access token.

    Args:
        payload: Admin OTP verification payload.

    Returns:
        Authenticated admin token response.

    Raises:
        HTTPException: If OTP verification fails.
    """

    try:
        logging.info("Calling /v1/admins/login/verify endpoint")
        return await UserController().verify_admin_login_otp(payload)
    except HTTPException as httperror:
        logging.error("Error in /v1/admins/login/verify endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/admins/login/verify endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify admin login OTP",
        )


@user_router.get(
    "/v1/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_profile(
    user_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserResponse:
    """Fetch one user profile.

    Args:
        user_id: User identifier whose profile is requested.
        token: JWT token provided in the Authorization header.

    Returns:
        Serialized user profile.

    Raises:
        HTTPException: If the token is invalid or access is not allowed.
    """

    try:
        logging.info("Calling /v1/users/%s endpoint", user_id)
        authenticated_user_details = _get_authenticated_user(token)
        if (
            authenticated_user_details.get("user_role") != "ADMIN"
            and authenticated_user_details.get("id") != user_id
        ):
            logging.warning(
                "Unauthorized access attempt to /v1/users/%s by user ID %s",
                user_id,
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await UserController().get_user_profile(user_id)
    except HTTPException as httperror:
        logging.error("Error in /v1/users/%s endpoint: %s", user_id, httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/users/%s endpoint: %s", user_id, error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user profile",
        )


@user_router.patch(
    "/v1/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def update_user_profile(
    user_id: str,
    payload: UserUpdateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserResponse:
    """Update one customer profile.

    Args:
        user_id: User identifier to update.
        payload: Partial user profile updates.
        token: JWT token provided in the Authorization header.

    Returns:
        Updated user profile response.

    Raises:
        HTTPException: If the token is invalid or access is not allowed.
    """

    try:
        logging.info("Calling PATCH /v1/users/%s endpoint", user_id)
        authenticated_user_details = _get_authenticated_user(token)
        if (
            authenticated_user_details.get("user_role") != "ADMIN"
            and authenticated_user_details.get("id") != user_id
        ):
            logging.warning(
                "Unauthorized update attempt to /v1/users/%s by user ID %s",
                user_id,
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this resource",
            )
        return await UserController().update_user_profile(user_id, payload)
    except HTTPException as httperror:
        logging.error("Error in PATCH /v1/users/%s endpoint: %s", user_id, httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in PATCH /v1/users/%s endpoint: %s", user_id, error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile",
        )


@user_router.patch(
    "/v1/admins/{user_id}",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
)
async def update_admin_profile(
    user_id: str,
    payload: AdminUpdateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> AdminResponse:
    """Update one admin profile.

    Args:
        user_id: Admin user identifier to update.
        payload: Partial admin profile updates.
        token: JWT token provided in the Authorization header.

    Returns:
        Updated admin profile response.

    Raises:
        HTTPException: If the token is invalid or the caller is not an admin.
    """

    try:
        logging.info("Calling PATCH /v1/admins/%s endpoint", user_id)
        authenticated_user_details = _get_authenticated_user(token)
        if authenticated_user_details.get("user_role") != "ADMIN":
            logging.warning(
                "Unauthorized access attempt to PATCH /v1/admins/%s by user ID %s",
                user_id,
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await UserController().update_admin_profile(user_id, payload)
    except HTTPException as httperror:
        logging.error("Error in PATCH /v1/admins/%s endpoint: %s", user_id, httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in PATCH /v1/admins/%s endpoint: %s", user_id, error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update admin profile",
        )


@user_router.get(
    "/v1/admins/users",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_users(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserListResponse:
    """Return all users for the customer-app admin dashboard.

    Args:
        token: JWT token provided in the Authorization header.

    Returns:
        Ordered user list response.

    Raises:
        HTTPException: If the token is invalid or the caller is not an admin.
    """

    try:
        logging.info("Calling GET /v1/admins/users endpoint")
        authenticated_user_details = _get_authenticated_user(token)
        if authenticated_user_details.get("user_role") != "ADMIN":
            logging.warning(
                "Unauthorized access attempt to GET /v1/admins/users by user ID %s",
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await UserController().list_users()
    except HTTPException as httperror:
        logging.error("Error in GET /v1/admins/users endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in GET /v1/admins/users endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users",
        )

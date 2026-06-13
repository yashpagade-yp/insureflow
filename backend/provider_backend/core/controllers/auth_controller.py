"""Controller logic for provider-admin authentication flows."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from commons.auth import (
    generate_otp,
    hash_otp,
    sign_jwt,
    verify_hashed_otp,
    verify_password,
)
from commons.logger import logger
from core.apis.schemas.request_schema.auth_request_schema import (
    ProviderAdminLoginRequest,
    ProviderAdminLoginVerifyRequest,
)
from core.apis.schemas.response_schema.auth_response_schema import (
    ProviderAdminLoginOtpResponse,
    ProviderAdminLoginVerifyResponse,
)
from core.cruds.provider_user_crud import ProviderUserCrud
from core.models.provider_user_model import (
    ProviderOtpPurpose,
    ProviderUserOtp,
)

logging = logger(__name__)

OTP_EXPIRY_MINUTES = 10
OTP_REQUEST_INTERVAL_SECONDS = 30
MAX_OTP_ATTEMPTS = 5
OTP_ATTEMPT_WINDOW_SECONDS = 3600


class ProviderAuthController:
    """Handles provider-admin login and OTP verification business logic."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependency."""

        self.provider_user_crud = ProviderUserCrud()

    async def start_login(
        self,
        payload: ProviderAdminLoginRequest,
    ) -> ProviderAdminLoginOtpResponse:
        """Validate password and create a fresh login OTP for a provider admin."""
        try:
            logging.info("Executing ProviderAuthController.start_login function")
            normalized_email = payload.email.strip().lower()
            provider_user = await self.provider_user_crud.get_by_email(normalized_email)
            if provider_user is None:
                logging.warning(
                    "Provider admin not found for email %s", normalized_email
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Provider admin not found.",
                )
            if not provider_user.is_active:
                logging.warning(
                    "Inactive provider admin attempted login for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Provider admin account is inactive.",
                )
            if not verify_password(payload.password, provider_user.password_hash):
                logging.warning(
                    "Invalid provider-admin credentials for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email or password.",
                )

            now = datetime.now(timezone.utc)
            if (
                provider_user.otp is not None
                and provider_user.otp.purpose == ProviderOtpPurpose.ADMIN_LOGIN
                and (now - provider_user.otp.requested_at).total_seconds()
                < OTP_REQUEST_INTERVAL_SECONDS
            ):
                logging.warning(
                    "Provider-admin OTP requested too frequently for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Please wait before requesting a new provider-admin OTP.",
                )

            plain_otp = generate_otp()
            otp_state = ProviderUserOtp(
                code_hash=hash_otp(plain_otp),
                purpose=ProviderOtpPurpose.ADMIN_LOGIN,
                expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES),
                requested_at=now,
                attempt_count=0,
                attempt_window_started_at=now,
            )
            await self.provider_user_crud.save_otp(provider_user, otp_state)
            logging.info(
                "Provider-admin OTP generated successfully for email %s",
                normalized_email,
            )
            return ProviderAdminLoginOtpResponse(
                message="Provider-admin OTP generated successfully.",
                email=provider_user.email,
                otp_expires_at=otp_state.expires_at,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in ProviderAuthController.start_login function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in ProviderAuthController.start_login function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start provider-admin login.",
            )

    async def verify_login(
        self,
        payload: ProviderAdminLoginVerifyRequest,
    ) -> ProviderAdminLoginVerifyResponse:
        """Verify provider-admin OTP and issue a JWT."""
        try:
            logging.info("Executing ProviderAuthController.verify_login function")
            normalized_email = payload.email.strip().lower()
            provider_user = await self.provider_user_crud.get_by_email(normalized_email)
            if provider_user is None or provider_user.otp is None:
                logging.warning(
                    "Provider-admin OTP not found for email %s", normalized_email
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Provider-admin OTP not found for this email.",
                )
            if not provider_user.is_active:
                logging.warning(
                    "Inactive provider admin attempted OTP verification for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Provider admin account is inactive.",
                )

            now = datetime.now(timezone.utc)
            provider_user.otp = self._reset_otp_attempt_window_if_needed(
                provider_user.otp,
                now,
            )
            if (
                provider_user.otp.purpose != ProviderOtpPurpose.ADMIN_LOGIN
                or provider_user.otp.expires_at < now
            ):
                logging.warning(
                    "Expired provider-admin OTP used for email %s", normalized_email
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provider-admin OTP has expired. Please request a new OTP.",
                )

            if provider_user.otp.attempt_count >= MAX_OTP_ATTEMPTS:
                logging.warning(
                    "Maximum provider-admin OTP attempts exceeded for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Maximum provider-admin OTP verification attempts exceeded. Please request a new OTP.",
                )

            if not verify_hashed_otp(payload.otp, provider_user.otp.code_hash):
                provider_user.otp.attempt_count += 1
                await self.provider_user_crud.save_otp(provider_user, provider_user.otp)
                logging.warning(
                    "Invalid provider-admin OTP submitted for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid provider-admin OTP.",
                )

            await self.provider_user_crud.clear_otp(provider_user)
            provider_user = await self.provider_user_crud.update_last_login_at(
                provider_user
            )
            access_token = sign_jwt(provider_user.user_role.value, str(provider_user.id))
            logging.info(
                "Provider-admin OTP verified successfully for email %s",
                normalized_email,
            )
            return ProviderAdminLoginVerifyResponse(
                message="Provider-admin OTP verified successfully.",
                access_token=access_token,
                token_type="bearer",
                admin_id=str(provider_user.id),
                email=provider_user.email,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in ProviderAuthController.verify_login function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in ProviderAuthController.verify_login function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify provider-admin login.",
            )

    def _reset_otp_attempt_window_if_needed(
        self,
        otp_state: ProviderUserOtp,
        now: datetime,
    ) -> ProviderUserOtp:
        """Reset provider-admin OTP attempts when the active window has expired."""

        if (
            now - otp_state.attempt_window_started_at
        ).total_seconds() >= OTP_ATTEMPT_WINDOW_SECONDS:
            otp_state.attempt_count = 0
            otp_state.attempt_window_started_at = now
        return otp_state

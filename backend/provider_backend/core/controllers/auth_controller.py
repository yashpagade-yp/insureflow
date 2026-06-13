"""Controller logic for provider-admin authentication flows."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from ...commons.auth import (
    generate_otp,
    hash_otp,
    sign_jwt,
    verify_hashed_otp,
    verify_password,
)
from ...commons.logger import logger
from ..apis.schemas.request_schema.auth_request_schema import (
    ProviderAdminLoginRequest,
    ProviderAdminLoginVerifyRequest,
)
from ..apis.schemas.response_schema.auth_response_schema import (
    ProviderAdminLoginOtpResponse,
    ProviderAdminLoginVerifyResponse,
)
from ..cruds.provider_user_crud import ProviderUserCrud
from ..models.provider_user_model import (
    ProviderOtpPurpose,
    ProviderUserOtp,
)

logging = logger(__name__)


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
            logging.info("Executing ProviderAuthController.start_login")
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

            plain_otp = generate_otp()
            now = datetime.now(timezone.utc)
            otp_state = ProviderUserOtp(
                code_hash=hash_otp(plain_otp),
                purpose=ProviderOtpPurpose.ADMIN_LOGIN,
                expires_at=now + timedelta(minutes=10),
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
        except HTTPException:
            raise
        except Exception as error:
            logging.error(
                "Error in ProviderAuthController.start_login: %s",
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
            logging.info("Executing ProviderAuthController.verify_login")
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
        except HTTPException:
            raise
        except Exception as error:
            logging.error(
                "Error in ProviderAuthController.verify_login: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify provider-admin login.",
            )

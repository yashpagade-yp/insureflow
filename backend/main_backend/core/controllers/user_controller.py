"""Controller logic for user and login-OTP flows in the main backend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from commons.auth import (
    generate_otp,
    hash_otp,
    log_otp_for_dev,
    signJWT,
    verify_hashed_otp,
    verify_password,
)
from commons.email import send_admin_otp_email
from commons.logger import logger
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
    UserAddressResponse,
    UserLoginOtpResponse,
    UserLoginVerifyResponse,
    UserResponse,
)
from core.cruds.user_crud import UserCrud
from core.models.user_model import Address, OtpPurpose, UserModel, UserOtp

logging = logger(__name__)

OTP_EXPIRY_MINUTES = 10
OTP_REQUEST_INTERVAL_SECONDS = 30
MAX_OTP_ATTEMPTS = 5
OTP_ATTEMPT_WINDOW_SECONDS = 3600


class UserController:
    """Handles user profile and customer login OTP business logic."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependency."""

        self.user_crud = UserCrud()

    async def send_login_otp(
        self,
        payload: UserLoginOtpRequest,
    ) -> UserLoginOtpResponse:
        """Create or find a user and store a fresh login OTP."""
        try:
            logging.info("Executing UserController.send_login_otp function")
            normalized_mobile_number = payload.mobile_number.strip()
            user = await self.user_crud.get_by_mobile_number(normalized_mobile_number)
            if user is None:
                user = await self.user_crud.create(
                    UserModel.model_validate(
                        {
                            "mobile_number": normalized_mobile_number,
                            "first_name": "Guest",
                            "last_name": "User",
                        }
                    )
                )

            now = datetime.now(timezone.utc)
            if user.otp is not None:
                user.otp = self._reset_otp_attempt_window_if_needed(user.otp, now)
            if (
                user.otp is not None
                and user.otp.purpose == OtpPurpose.USER_LOGIN
                and (now - user.otp.requested_at).total_seconds()
                < OTP_REQUEST_INTERVAL_SECONDS
            ):
                logging.warning(
                    "Login OTP requested too frequently for mobile number %s",
                    normalized_mobile_number,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Please wait before requesting a new login OTP.",
                )

            plain_otp = generate_otp()
            log_otp_for_dev(
                flow_name="customer_login",
                recipient=normalized_mobile_number,
                otp=plain_otp,
            )
            otp_state = UserOtp(
                code_hash=hash_otp(plain_otp),
                purpose=OtpPurpose.USER_LOGIN,
                expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES),
                requested_at=now,
                attempt_count=0,
                attempt_window_started_at=now,
            )
            await self.user_crud.save_otp(user, otp_state)
            logging.info(
                "Login OTP generated successfully for mobile number %s",
                normalized_mobile_number,
            )
            return UserLoginOtpResponse(
                message="Login OTP generated successfully.",
                mobile_number=user.mobile_number,
                otp_expires_at=otp_state.expires_at,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in UserController.send_login_otp function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in UserController.send_login_otp function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate login OTP.",
            )

    async def verify_login_otp(
        self,
        payload: UserLoginVerifyRequest,
    ) -> UserLoginVerifyResponse:
        """Verify a stored login OTP and issue a JWT."""
        try:
            logging.info("Executing UserController.verify_login_otp function")
            normalized_mobile_number = payload.mobile_number.strip()
            user = await self.user_crud.get_by_mobile_number(normalized_mobile_number)
            if user is None or user.otp is None:
                logging.warning(
                    "Login OTP not found for mobile number %s",
                    normalized_mobile_number,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Login OTP not found for this mobile number.",
                )

            now = datetime.now(timezone.utc)
            user.otp = self._reset_otp_attempt_window_if_needed(user.otp, now)
            if user.otp.purpose != OtpPurpose.USER_LOGIN or user.otp.expires_at < now:
                logging.warning(
                    "Expired login OTP used for mobile number %s",
                    normalized_mobile_number,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Login OTP has expired. Please request a new OTP.",
                )

            if user.otp.attempt_count >= MAX_OTP_ATTEMPTS:
                logging.warning(
                    "Maximum login OTP attempts exceeded for mobile number %s",
                    normalized_mobile_number,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Maximum login OTP verification attempts exceeded. Please request a new OTP.",
                )

            if not verify_hashed_otp(payload.otp, user.otp.code_hash):
                user.otp.attempt_count += 1
                await self.user_crud.save_otp(user, user.otp)
                logging.warning(
                    "Invalid login OTP submitted for mobile number %s",
                    normalized_mobile_number,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid login OTP.",
                )

            await self.user_crud.clear_otp(user)
            user = await self.user_crud.update_last_login_at(user)
            access_token = signJWT(user.user_role.value, str(user.id))
            logging.info(
                "Login OTP verified successfully for mobile number %s",
                normalized_mobile_number,
            )
            return UserLoginVerifyResponse(
                message="Login OTP verified successfully.",
                access_token=access_token,
                token_type="bearer",
                user_id=str(user.id),
                mobile_number=user.mobile_number,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in UserController.verify_login_otp function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in UserController.verify_login_otp function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify login OTP.",
            )

    async def send_admin_login_otp(
        self,
        payload: AdminLoginRequest,
    ) -> AdminLoginOtpResponse:
        """Validate admin credentials and store a fresh admin login OTP."""

        try:
            logging.info("Executing UserController.send_admin_login_otp function")
            normalized_email = payload.email.strip().lower()
            admin_user = await self.user_crud.get_admin_by_email(normalized_email)
            if admin_user is None or admin_user.password is None:
                logging.warning(
                    "Admin login attempted with unknown email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid admin email or password.",
                )

            if not verify_password(payload.password, admin_user.password):
                logging.warning(
                    "Invalid admin password submitted for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid admin email or password.",
                )

            now = datetime.now(timezone.utc)
            if admin_user.otp is not None:
                admin_user.otp = self._reset_otp_attempt_window_if_needed(
                    admin_user.otp,
                    now,
                )
            if (
                admin_user.otp is not None
                and admin_user.otp.purpose == OtpPurpose.ADMIN_LOGIN
                and (now - admin_user.otp.requested_at).total_seconds()
                < OTP_REQUEST_INTERVAL_SECONDS
            ):
                logging.warning(
                    "Admin OTP requested too frequently for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Please wait before requesting a new admin OTP.",
                )

            plain_otp = generate_otp()
            log_otp_for_dev(
                flow_name="main_admin_login",
                recipient=normalized_email,
                otp=plain_otp,
            )
            otp_state = UserOtp(
                code_hash=hash_otp(plain_otp),
                purpose=OtpPurpose.ADMIN_LOGIN,
                expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES),
                requested_at=now,
                attempt_count=0,
                attempt_window_started_at=now,
            )
            await self.user_crud.save_otp(admin_user, otp_state)
            try:
                send_admin_otp_email(normalized_email, plain_otp)
            except Exception as error:
                await self.user_crud.clear_otp(admin_user)
                logging.error(
                    "Failed to deliver admin OTP email for %s: %s",
                    normalized_email,
                    error,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to deliver admin login OTP email.",
                )
            logging.info(
                "Admin login OTP generated successfully for email %s",
                normalized_email,
            )
            return AdminLoginOtpResponse(
                message="Admin login OTP generated successfully.",
                email=normalized_email,
                otp_expires_at=otp_state.expires_at,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in UserController.send_admin_login_otp function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in UserController.send_admin_login_otp function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate admin login OTP.",
            )

    async def verify_admin_login_otp(
        self,
        payload: AdminLoginVerifyRequest,
    ) -> AdminLoginVerifyResponse:
        """Verify a stored admin login OTP and issue a JWT."""

        try:
            logging.info("Executing UserController.verify_admin_login_otp function")
            normalized_email = payload.email.strip().lower()
            admin_user = await self.user_crud.get_admin_by_email(normalized_email)
            if admin_user is None or admin_user.otp is None:
                logging.warning(
                    "Admin login OTP not found for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin login OTP not found for this email.",
                )

            now = datetime.now(timezone.utc)
            admin_user.otp = self._reset_otp_attempt_window_if_needed(admin_user.otp, now)
            if (
                admin_user.otp.purpose != OtpPurpose.ADMIN_LOGIN
                or admin_user.otp.expires_at < now
            ):
                logging.warning(
                    "Expired admin login OTP used for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Admin login OTP has expired. Please request a new OTP.",
                )

            if admin_user.otp.attempt_count >= MAX_OTP_ATTEMPTS:
                logging.warning(
                    "Maximum admin login OTP attempts exceeded for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Maximum admin OTP verification attempts exceeded. Please request a new OTP.",
                )

            if not verify_hashed_otp(payload.otp, admin_user.otp.code_hash):
                admin_user.otp.attempt_count += 1
                await self.user_crud.save_otp(admin_user, admin_user.otp)
                logging.warning(
                    "Invalid admin login OTP submitted for email %s",
                    normalized_email,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid admin login OTP.",
                )

            await self.user_crud.clear_otp(admin_user)
            admin_user = await self.user_crud.update_last_login_at(admin_user)
            access_token = signJWT(admin_user.user_role.value, str(admin_user.id))
            logging.info(
                "Admin login OTP verified successfully for email %s",
                normalized_email,
            )
            return AdminLoginVerifyResponse(
                message="Admin login OTP verified successfully.",
                access_token=access_token,
                token_type="bearer",
                admin_id=str(admin_user.id),
                email=normalized_email,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in UserController.verify_admin_login_otp function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in UserController.verify_admin_login_otp function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify admin login OTP.",
            )

    def _reset_otp_attempt_window_if_needed(
        self,
        otp_state: UserOtp,
        now: datetime,
    ) -> UserOtp:
        """Reset OTP attempt tracking when the active attempt window has expired."""

        otp_state.requested_at = self._ensure_utc_datetime(otp_state.requested_at)
        otp_state.expires_at = self._ensure_utc_datetime(otp_state.expires_at)
        otp_state.attempt_window_started_at = self._ensure_utc_datetime(
            otp_state.attempt_window_started_at
        )
        if (
            now - otp_state.attempt_window_started_at
        ).total_seconds() >= OTP_ATTEMPT_WINDOW_SECONDS:
            otp_state.attempt_count = 0
            otp_state.attempt_window_started_at = now
        return otp_state

    def _ensure_utc_datetime(self, value: datetime) -> datetime:
        """Normalize stored datetimes so comparisons always use UTC-aware values."""

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    async def get_user_profile(self, user_id: str) -> UserResponse:
        """Return one user profile."""
        try:
            logging.info("Executing UserController.get_user_profile function")
            user = await self.user_crud.get_by_id(user_id)
            if user is None:
                logging.warning("User not found for id %s", user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )

            return self._build_user_response(user)
        except HTTPException as httperror:
            logging.error(
                "Error in UserController.get_user_profile function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in UserController.get_user_profile function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user profile.",
            )

    async def update_user_profile(
        self,
        user_id: str,
        payload: UserUpdateRequest,
    ) -> UserResponse:
        """Apply partial profile updates to one user."""
        try:
            logging.info("Executing UserController.update_user_profile function")
            user = await self.user_crud.get_by_id(user_id)
            if user is None:
                logging.warning("User not found for id %s during update", user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )

            updates = payload.model_dump(exclude_unset=True)
            if "address" in updates and updates["address"] is not None:
                updates["address"] = Address.model_validate(updates["address"])

            updated_user = await self.user_crud.update(user, updates)
            logging.info("User profile updated successfully for id %s", user_id)
            return self._build_user_response(updated_user)
        except HTTPException as httperror:
            logging.error(
                "Error in UserController.update_user_profile function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in UserController.update_user_profile function: %s", error
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile.",
            )

    async def update_admin_profile(
        self,
        user_id: str,
        payload: AdminUpdateRequest,
    ) -> AdminResponse:
        """Apply partial profile updates to one admin user."""
        try:
            logging.info("Executing UserController.update_admin_profile function")
            user = await self.user_crud.get_by_id(user_id)
            if user is None:
                logging.warning("Admin not found for id %s during update", user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin not found.",
                )

            updated_user = await self.user_crud.update(
                user,
                payload.model_dump(exclude_unset=True),
            )
            logging.info("Admin profile updated successfully for id %s", user_id)
            return self._build_admin_response(updated_user)
        except HTTPException as httperror:
            logging.error(
                "Error in UserController.update_admin_profile function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in UserController.update_admin_profile function: %s", error
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update admin profile.",
            )

    def _build_user_response(self, user: UserModel) -> UserResponse:
        """Convert a user document into the public user response schema."""

        address_response = None
        if user.address is not None:
            address_response = UserAddressResponse(
                street=user.address.street,
                city=user.address.city,
                state=user.address.state,
                postal_code=user.address.postal_code,
                country=user.address.country,
            )

        return UserResponse(
            id=str(user.id),
            mobile_number=user.mobile_number,
            first_name=user.first_name,
            last_name=user.last_name,
            user_role=user.user_role.value,
            email=user.email,
            dob=user.dob,
            address=address_response,
            user_metadata=user.user_metadata,
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _build_admin_response(self, user: UserModel) -> AdminResponse:
        """Convert a user document into the public admin response schema."""

        if user.email is None:
            logging.error(
                "Admin user %s is missing an email address during response build",
                str(user.id),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Admin user is missing a required email address.",
            )

        return AdminResponse(
            id=str(user.id),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            mobile_number=user.mobile_number,
            user_role=user.user_role.value,
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

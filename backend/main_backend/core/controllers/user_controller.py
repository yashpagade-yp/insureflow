"""Controller logic for user and login-OTP flows in the main backend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from ...commons.auth import generate_otp, hash_otp, signJWT, verify_hashed_otp
from ...commons.logger import logger
from ..apis.schemas.request_schema.user_request_schema import (
    AdminUpdateRequest,
    UserLoginOtpRequest,
    UserLoginVerifyRequest,
    UserUpdateRequest,
)
from ..apis.schemas.response_schema.user_response_schema import (
    AdminResponse,
    UserAddressResponse,
    UserLoginOtpResponse,
    UserLoginVerifyResponse,
    UserResponse,
)
from ..cruds.user_crud import UserCrud
from ..models.user_model import Address, OtpPurpose, UserModel, UserOtp

logging = logger(__name__)


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
            logging.info("Executing UserController.send_login_otp")
            user = await self.user_crud.get_by_mobile_number(payload.mobile_number)
            if user is None:
                user = await self.user_crud.create(
                    UserModel(
                        mobile_number=payload.mobile_number,
                        first_name="Guest",
                        last_name="User",
                    )
                )

            plain_otp = generate_otp()
            now = datetime.now(timezone.utc)
            otp_state = UserOtp(
                code_hash=hash_otp(plain_otp),
                purpose=OtpPurpose.USER_LOGIN,
                expires_at=now + timedelta(minutes=10),
                requested_at=now,
                attempt_count=0,
                attempt_window_started_at=now,
            )
            await self.user_crud.save_otp(user, otp_state)
            logging.info(
                "Login OTP generated successfully for mobile number %s",
                payload.mobile_number,
            )
            return UserLoginOtpResponse(
                message="Login OTP generated successfully.",
                mobile_number=user.mobile_number,
                otp_expires_at=otp_state.expires_at,
            )
        except HTTPException:
            raise
        except Exception as error:
            logging.error("Error in UserController.send_login_otp: %s", error)
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
            logging.info("Executing UserController.verify_login_otp")
            user = await self.user_crud.get_by_mobile_number(payload.mobile_number)
            if user is None or user.otp is None:
                logging.warning(
                    "Login OTP not found for mobile number %s",
                    payload.mobile_number,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Login OTP not found for this mobile number.",
                )

            now = datetime.now(timezone.utc)
            if user.otp.purpose != OtpPurpose.USER_LOGIN or user.otp.expires_at < now:
                logging.warning(
                    "Expired login OTP used for mobile number %s",
                    payload.mobile_number,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Login OTP has expired. Please request a new OTP.",
                )

            if not verify_hashed_otp(payload.otp, user.otp.code_hash):
                user.otp.attempt_count += 1
                await self.user_crud.save_otp(user, user.otp)
                logging.warning(
                    "Invalid login OTP submitted for mobile number %s",
                    payload.mobile_number,
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
                payload.mobile_number,
            )
            return UserLoginVerifyResponse(
                message="Login OTP verified successfully.",
                access_token=access_token,
                token_type="bearer",
                user_id=str(user.id),
                mobile_number=user.mobile_number,
            )
        except HTTPException:
            raise
        except Exception as error:
            logging.error("Error in UserController.verify_login_otp: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify login OTP.",
            )

    async def get_user_profile(self, user_id: str) -> UserResponse:
        """Return one user profile."""
        try:
            logging.info("Executing UserController.get_user_profile")
            user = await self.user_crud.get_by_id(user_id)
            if user is None:
                logging.warning("User not found for id %s", user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )

            return self._build_user_response(user)
        except HTTPException:
            raise
        except Exception as error:
            logging.error("Error in UserController.get_user_profile: %s", error)
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
            logging.info("Executing UserController.update_user_profile")
            user = await self.user_crud.get_by_id(user_id)
            if user is None:
                logging.warning("User not found for id %s during update", user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )

            updates = payload.model_dump(exclude_unset=True)
            if "address" in updates and updates["address"] is not None:
                updates["address"] = Address(**updates["address"])

            updated_user = await self.user_crud.update(user, updates)
            logging.info("User profile updated successfully for id %s", user_id)
            return self._build_user_response(updated_user)
        except HTTPException:
            raise
        except Exception as error:
            logging.error("Error in UserController.update_user_profile: %s", error)
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
            logging.info("Executing UserController.update_admin_profile")
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
        except HTTPException:
            raise
        except Exception as error:
            logging.error("Error in UserController.update_admin_profile: %s", error)
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

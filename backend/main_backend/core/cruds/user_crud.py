"""CRUD helpers for user documents in the main backend.

This module contains database-only operations for the ``User`` model. Business
rules such as OTP generation, token creation, or authorization stay outside the
CRUD layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from odmantic import ObjectId

from commons.logger import logger
from core.database.database import get_engine
from core.models.user_model import UserModel, UserOtp, UserRole

logging = logger(__name__)


class UserCrud:
    """Provides database operations for user documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, user: UserModel) -> UserModel:
        """Persist a new user document."""
        try:
            logging.info("Executing UserCrud.create function")
            await self.engine.save(user)
            return user
        except Exception as error:
            logging.error("Error in UserCrud.create function: %s", error)
            raise

    async def get_by_id(self, user_id: str | ObjectId) -> UserModel | None:
        """Return one user by ODMantic object id."""
        try:
            logging.info("Executing UserCrud.get_by_id function")
            if isinstance(user_id, str):
                if len(user_id) != 24:
                    return None
                user_id = ObjectId(user_id)
            return await self.engine.find_one(UserModel, UserModel.id == user_id)
        except Exception as error:
            logging.error("Error in UserCrud.get_by_id function: %s", error)
            raise

    async def get_by_mobile_number(self, mobile_number: str) -> UserModel | None:
        """Return one user by mobile number."""
        try:
            logging.info("Executing UserCrud.get_by_mobile_number function")
            return await self.engine.find_one(
                UserModel,
                UserModel.mobile_number == mobile_number,
            )
        except Exception as error:
            logging.error("Error in UserCrud.get_by_mobile_number function: %s", error)
            raise

    async def get_admin_by_email(self, email: str) -> UserModel | None:
        """Return one admin user by email address."""
        try:
            logging.info("Executing UserCrud.get_admin_by_email function")
            return await self.engine.find_one(
                UserModel,
                (UserModel.email == email) & (UserModel.user_role == UserRole.ADMIN),
            )
        except Exception as error:
            logging.error("Error in UserCrud.get_admin_by_email function: %s", error)
            raise

    async def list_all(self) -> list[UserModel]:
        """Return all users, newest first."""

        try:
            logging.info("Executing UserCrud.list_all function")
            users = await self.engine.find(UserModel)
            return sorted(users, key=lambda item: item.updated_at, reverse=True)
        except Exception as error:
            logging.error("Error in UserCrud.list_all function: %s", error)
            raise

    async def update(self, user: UserModel, updates: dict[str, Any]) -> UserModel:
        """Apply partial updates to a user document and save it."""
        try:
            logging.info("Executing UserCrud.update function")
            for field_name, field_value in updates.items():
                setattr(user, field_name, field_value)

            user.updated_at = datetime.now(timezone.utc)
            await self.engine.save(user)
            return user
        except Exception as error:
            logging.error("Error in UserCrud.update function: %s", error)
            raise

    async def save_otp(self, user: UserModel, otp: UserOtp) -> UserModel:
        """Store or replace the current login OTP on a user document."""
        try:
            logging.info("Executing UserCrud.save_otp function")
            user.otp = otp
            user.updated_at = datetime.now(timezone.utc)
            await self.engine.save(user)
            return user
        except Exception as error:
            logging.error("Error in UserCrud.save_otp function: %s", error)
            raise

    async def clear_otp(self, user: UserModel) -> UserModel:
        """Remove the current login OTP from a user document."""
        try:
            logging.info("Executing UserCrud.clear_otp function")
            user.otp = None
            user.updated_at = datetime.now(timezone.utc)
            await self.engine.save(user)
            return user
        except Exception as error:
            logging.error("Error in UserCrud.clear_otp function: %s", error)
            raise

    async def update_last_login_at(self, user: UserModel) -> UserModel:
        """Update the latest-login timestamp for a user document."""
        try:
            logging.info("Executing UserCrud.update_last_login_at function")
            now = datetime.now(timezone.utc)
            user.last_login_at = now
            user.updated_at = now
            await self.engine.save(user)
            return user
        except Exception as error:
            logging.error("Error in UserCrud.update_last_login_at function: %s", error)
            raise

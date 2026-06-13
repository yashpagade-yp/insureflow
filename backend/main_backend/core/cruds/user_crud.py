"""CRUD helpers for user documents in the main backend.

This module contains database-only operations for the ``User`` model. Business
rules such as OTP generation, token creation, or authorization stay outside the
CRUD layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from odmantic import ObjectId

from ..database.database import get_engine
from ..models.user_model import UserModel, UserOtp, UserRole


class UserCrud:
    """Provides database operations for user documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, user: UserModel) -> UserModel:
        """Persist a new user document."""

        await self.engine.save(user)
        return user

    async def get_by_id(self, user_id: str | ObjectId) -> UserModel | None:
        """Return one user by ODMantic object id."""

        return await self.engine.find_one(UserModel, UserModel.id == user_id)

    async def get_by_mobile_number(self, mobile_number: str) -> UserModel | None:
        """Return one user by mobile number."""

        return await self.engine.find_one(
            UserModel,
            UserModel.mobile_number == mobile_number,
        )

    async def get_admin_by_email(self, email: str) -> UserModel | None:
        """Return one admin user by email address."""

        return await self.engine.find_one(
            UserModel,
            (UserModel.email == email) & (UserModel.user_role == UserRole.ADMIN),
        )

    async def update(self, user: UserModel, updates: dict[str, Any]) -> UserModel:
        """Apply partial updates to a user document and save it."""

        for field_name, field_value in updates.items():
            setattr(user, field_name, field_value)

        user.updated_at = datetime.now(timezone.utc)
        await self.engine.save(user)
        return user

    async def save_otp(self, user: UserModel, otp: UserOtp) -> UserModel:
        """Store or replace the current login OTP on a user document."""

        user.otp = otp
        user.updated_at = datetime.now(timezone.utc)
        await self.engine.save(user)
        return user

    async def clear_otp(self, user: UserModel) -> UserModel:
        """Remove the current login OTP from a user document."""

        user.otp = None
        user.updated_at = datetime.now(timezone.utc)
        await self.engine.save(user)
        return user

    async def update_last_login_at(self, user: UserModel) -> UserModel:
        """Update the latest-login timestamp for a user document."""

        now = datetime.now(timezone.utc)
        user.last_login_at = now
        user.updated_at = now
        await self.engine.save(user)
        return user

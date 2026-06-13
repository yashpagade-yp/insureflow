"""CRUD helpers for provider-admin user documents in the provider backend.

This module contains database-only operations for the ``ProviderUser`` model.
Business rules such as password verification, OTP generation, token creation,
and authorization stay outside the CRUD layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from odmantic import ObjectId

from ..database.database import get_engine
from ..models.provider_user_model import ProviderUserModel, ProviderUserOtp


class ProviderUserCrud:
    """Provides database operations for provider-admin user documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, provider_user: ProviderUserModel) -> ProviderUserModel:
        """Persist a new provider-admin user document."""

        await self.engine.save(provider_user)
        return provider_user

    async def get_by_id(
        self,
        provider_user_id: str | ObjectId,
    ) -> ProviderUserModel | None:
        """Return one provider-admin user by ODMantic object id."""

        return await self.engine.find_one(
            ProviderUserModel,
            ProviderUserModel.id == provider_user_id,
        )

    async def get_by_email(self, email: str) -> ProviderUserModel | None:
        """Return one provider-admin user by email address."""

        return await self.engine.find_one(
            ProviderUserModel,
            ProviderUserModel.email == email,
        )

    async def list_all(self) -> list[ProviderUserModel]:
        """Return all provider-admin users, newest first."""

        users = await self.engine.find(ProviderUserModel)
        return sorted(users, key=lambda item: item.created_at, reverse=True)

    async def update(
        self,
        provider_user: ProviderUserModel,
        updates: dict[str, Any],
    ) -> ProviderUserModel:
        """Apply partial updates to a provider-admin user document and save it."""

        for field_name, field_value in updates.items():
            setattr(provider_user, field_name, field_value)

        provider_user.updated_at = datetime.now(timezone.utc)
        await self.engine.save(provider_user)
        return provider_user

    async def save_otp(
        self,
        provider_user: ProviderUserModel,
        otp: ProviderUserOtp,
    ) -> ProviderUserModel:
        """Store or replace the current login OTP on a provider-admin user."""

        provider_user.otp = otp
        provider_user.updated_at = datetime.now(timezone.utc)
        await self.engine.save(provider_user)
        return provider_user

    async def clear_otp(self, provider_user: ProviderUserModel) -> ProviderUserModel:
        """Remove the current login OTP from a provider-admin user document."""

        provider_user.otp = None
        provider_user.updated_at = datetime.now(timezone.utc)
        await self.engine.save(provider_user)
        return provider_user

    async def update_last_login_at(
        self,
        provider_user: ProviderUserModel,
    ) -> ProviderUserModel:
        """Update the latest-login timestamp for a provider-admin user."""

        now = datetime.now(timezone.utc)
        provider_user.last_login_at = now
        provider_user.updated_at = now
        await self.engine.save(provider_user)
        return provider_user

"""Provider-side admin user models for the InsureFlow provider backend.

This module contains the login identity model used for the provider admin
frontend. In the current project flow, these users are internal admin users
who manage provider companies, broker registration, plans, quotes, payments,
and other provider-backend operations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from odmantic.config import ODMConfigDict
from pydantic import BaseModel, EmailStr


class ProviderUserRole(str, Enum):
    """Defines the supported roles for provider-backend users.

    Attributes:
        ADMIN: Full-access admin user for provider-backend operations.
    """

    ADMIN = "ADMIN"


class ProviderOtpPurpose(str, Enum):
    """Defines the supported OTP purposes for provider-side users.

    Attributes:
        ADMIN_LOGIN: OTP flow used during provider-admin login.
    """

    ADMIN_LOGIN = "admin_login"


class ProviderUserOtp(BaseModel):
    """Represents the active OTP state stored inside a provider user document.

    Attributes:
        code_hash: Hashed OTP value. Plain OTP values must never be stored.
        purpose: Business purpose of the current OTP.
        expires_at: Timestamp when the OTP becomes invalid.
        requested_at: Timestamp when the OTP was generated.
        attempt_count: Failed verification attempts in the active window.
        attempt_window_started_at: Timestamp when the current attempt window
            started.
    """

    code_hash: str = Field(..., description="Hashed active OTP")
    purpose: ProviderOtpPurpose = Field(..., description="Purpose for the active OTP")
    expires_at: datetime = Field(..., description="Timestamp when the OTP expires")
    requested_at: datetime = Field(
        ...,
        description="Timestamp when the OTP was last requested",
    )
    attempt_count: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Number of failed OTP verification attempts in the active window",
    )
    attempt_window_started_at: datetime = Field(
        ...,
        description="Timestamp when the current OTP attempt window started",
    )


class ProviderUser(Model):
    """Represents a provider-backend admin user stored in the `provider_users` collection.

    These users authenticate with email, password, and OTP before accessing the
    provider admin frontend. The same admin can manage provider companies,
    broker registration, plans, quotes, payments, and provider-side operations.

    Attributes:
        first_name: Admin user's given name.
        last_name: Admin user's family name.
        email: Unique email address used for provider-side login.
        mobile_number: Optional contact mobile number for the admin user.
        password_hash: Hashed password used for provider-side login.
        user_role: Assigned role for the provider-side user.
        otp: Optional active OTP state for admin login.
        is_active: Whether the provider-side user account is currently active.
        last_login_at: Timestamp of the latest successful login.
        created_at: UTC timestamp when the provider user was created.
        updated_at: UTC timestamp when the provider user was last updated.
    """

    first_name: str = Field(..., description="Provider admin first name")
    last_name: str = Field(..., description="Provider admin last name")
    email: EmailStr = Field(
        ...,
        unique=True,
        description="Unique email address used for provider-side login",
    )
    mobile_number: str | None = Field(
        default=None,
        description="Optional contact mobile number for the provider admin",
    )
    password_hash: str = Field(
        ...,
        description="Hashed password used for provider-side login",
    )
    user_role: ProviderUserRole = Field(
        default=ProviderUserRole.ADMIN,
        description="Assigned role for the provider-side user",
    )
    otp: ProviderUserOtp | None = Field(
        default=None,
        description="Active OTP state for provider-admin authentication",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the provider-side user account is active",
    )
    last_login_at: datetime | None = Field(
        default=None,
        description="Timestamp of the latest successful provider-side login",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the provider user was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the provider user was last updated",
    )

    model_config = ODMConfigDict(
        collection="provider_users",
        extra="forbid",
    )


ProviderUserModel = ProviderUser

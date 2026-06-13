"""User models for the InsureFlow main backend.

This module contains the `User` document model and the embedded sub-models
stored inside the `users` collection. The structure follows the current
InsureFlow specification while keeping the ODMantic-based pattern used by the
project.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from odmantic import Field, Model
from odmantic.config import ODMConfigDict
from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    """Defines the supported roles for InsureFlow users.

    Attributes:
        USER: Standard customer account authenticated through mobile and OTP.
        ADMIN: Internal admin account authenticated through email, password,
            and OTP.
    """

    USER = "USER"
    ADMIN = "ADMIN"


class OtpPurpose(str, Enum):
    """Defines the supported purposes for the active OTP state.

    Attributes:
        USER_LOGIN: OTP flow used for customer login.
        ADMIN_LOGIN: OTP flow used for admin login.
    """

    USER_LOGIN = "user_login"
    ADMIN_LOGIN = "admin_login"


class Address(BaseModel):
    """Represents the user's embedded postal address details.

    Attributes:
        street: Street address line.
        city: City name.
        state: State or province name.
        postal_code: Postal or ZIP code.
        country: Country name.
    """

    street: str = Field(..., description="Street address line")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State or province")
    postal_code: str = Field(..., description="Postal or ZIP code")
    country: str = Field(..., description="Country name")


class UserOtp(BaseModel):
    """Represents the active OTP state stored inside a user document.

    Attributes:
        code_hash: Hashed OTP value. Plain OTP values must never be stored.
        purpose: Business purpose of the current OTP.
        expires_at: Timestamp at which the OTP becomes invalid.
        requested_at: Timestamp when the OTP was generated.
        attempt_count: Failed verification attempts in the active window.
        attempt_window_started_at: Timestamp when the current attempt window
            started.
    """

    code_hash: str = Field(..., description="Hashed active OTP")
    purpose: OtpPurpose = Field(..., description="Purpose for the active OTP")
    expires_at: datetime = Field(..., description="Timestamp when the OTP expires")
    requested_at: datetime = Field(
        ..., description="Timestamp when the OTP was last requested"
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


class User(Model):
    """Represents a user document stored in the `users` collection.

    This model supports both customer and admin accounts. Customer users are
    expected to authenticate primarily through mobile number and OTP, while
    admin users can additionally use email and password.

    Attributes:
        mobile_number: Primary mobile number for the user.
        first_name: User's given name.
        last_name: User's family name.
        user_role: Assigned system role for the user.
        email: Optional admin email address. Kept optional to support normal
            user accounts that do not require email-based login.
        password: Optional hashed password, mainly for admin users.
        dob: Optional date of birth.
        address: Optional embedded postal address.
        user_metadata: Optional dictionary for extensible user-related data.
        otp: Optional embedded OTP state for authentication flows.
        is_active: Whether the user account is currently active.
        last_login_at: Optional UTC timestamp for the user's latest login.
        created_at: UTC timestamp for when the user record was created.
        updated_at: UTC timestamp for the last user record update.
    """

    mobile_number: str = Field(..., description="Primary mobile number for the user")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    user_role: UserRole = Field(
        default=UserRole.USER,
        description="Role assigned to the user in the system",
    )
    email: Optional[EmailStr] = Field(
        default=None,
        unique=True,
        description="Optional unique email address, mainly for admin login",
    )
    password: Optional[str] = Field(
        default=None,
        description="Optional hashed password, mainly for admin users",
    )
    dob: Optional[date] = Field(default=None, description="User's date of birth")
    address: Optional[Address] = Field(
        default=None,
        description="Embedded postal address for the user",
    )
    user_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the user",
    )
    otp: Optional[UserOtp] = Field(
        default=None,
        description="Active OTP state for authentication flows",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the user account is currently active",
    )
    last_login_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the user's latest successful login",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the user was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the user was last updated",
    )

    model_config = ODMConfigDict(
        collection="users",
        extra="forbid",
    )


UserModel = User

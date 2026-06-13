"""Response schemas for user- and admin-related APIs in the main backend.

This module contains response payloads aligned with the current InsureFlow
flow:

- customers may request login OTP later using mobile number
- customers may verify login OTP to access status, resume flow, or policy
  documents
- admins are created and managed separately
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserAddressResponse(BaseModel):
    """Represents structured address information returned for a user.

    Attributes:
        street: Street address line.
        city: City name.
        state: State or province name.
        postal_code: Postal or PIN code.
        country: Country name.
    """

    street: str = Field(..., description="Street address line")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State or province name")
    postal_code: str = Field(..., description="Postal or PIN code")
    country: str = Field(..., description="Country name")

    model_config = ConfigDict(extra="forbid")


class UserLoginOtpResponse(BaseModel):
    """Response payload returned after a login OTP is requested.

    Attributes:
        message: Human-readable response message.
        mobile_number: Customer mobile number to which the OTP was sent.
        otp_expires_at: Timestamp when the login OTP expires.
    """

    message: str = Field(..., description="Human-readable response message")
    mobile_number: str = Field(..., description="Customer mobile number that received the OTP")
    otp_expires_at: datetime = Field(..., description="Timestamp when the login OTP expires")

    model_config = ConfigDict(extra="forbid")


class UserLoginVerifyResponse(BaseModel):
    """Response payload returned after successful login OTP verification.

    Attributes:
        message: Human-readable response message.
        access_token: JWT access token for the authenticated user.
        token_type: Token type returned to the client.
        user_id: Authenticated user's identifier.
        mobile_number: Authenticated user's mobile number.
    """

    message: str = Field(..., description="Human-readable response message")
    access_token: str = Field(..., description="JWT access token for the authenticated user")
    token_type: str = Field(default="bearer", description="Token type returned to the client")
    user_id: str = Field(..., description="Authenticated user's identifier")
    mobile_number: str = Field(..., description="Authenticated user's mobile number")

    model_config = ConfigDict(extra="forbid")


class UserResponse(BaseModel):
    """Represents user details returned by the main backend.

    Attributes:
        id: User identifier.
        mobile_number: Primary mobile number of the user.
        first_name: User's given name.
        last_name: User's family name.
        user_role: Assigned system role of the user.
        email: Optional email address for the user.
        dob: Optional date of birth.
        address: Optional structured address of the user.
        user_metadata: Optional additional metadata for the user.
        is_active: Whether the user account is active.
        last_login_at: Timestamp of the user's latest successful login.
        created_at: Timestamp when the user was created.
        updated_at: Timestamp when the user was last updated.
    """

    id: str = Field(..., description="User identifier")
    mobile_number: str = Field(..., description="Primary mobile number of the user")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    user_role: str = Field(..., description="Assigned system role of the user")
    email: EmailStr | None = Field(default=None, description="Optional email address of the user")
    dob: date | None = Field(default=None, description="Optional date of birth of the user")
    address: UserAddressResponse | None = Field(
        default=None,
        description="Optional structured address of the user",
    )
    user_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional additional metadata about the user",
    )
    is_active: bool = Field(..., description="Whether the user account is active")
    last_login_at: datetime | None = Field(
        default=None,
        description="Timestamp of the user's latest successful login",
    )
    created_at: datetime = Field(..., description="Timestamp when the user was created")
    updated_at: datetime = Field(..., description="Timestamp when the user was last updated")

    model_config = ConfigDict(extra="forbid")


class AdminResponse(BaseModel):
    """Represents admin details returned by the main backend.

    Attributes:
        id: Admin identifier.
        first_name: Admin's given name.
        last_name: Admin's family name.
        email: Admin email used for login.
        mobile_number: Admin contact mobile number.
        user_role: Assigned system role of the admin.
        is_active: Whether the admin account is active.
        last_login_at: Timestamp of the admin's latest successful login.
        created_at: Timestamp when the admin was created.
        updated_at: Timestamp when the admin was last updated.
    """

    id: str = Field(..., description="Admin identifier")
    first_name: str = Field(..., description="Admin's first name")
    last_name: str = Field(..., description="Admin's last name")
    email: EmailStr = Field(..., description="Admin email used for login")
    mobile_number: str = Field(..., description="Admin contact mobile number")
    user_role: str = Field(..., description="Assigned system role of the admin")
    is_active: bool = Field(..., description="Whether the admin account is active")
    last_login_at: datetime | None = Field(
        default=None,
        description="Timestamp of the admin's latest successful login",
    )
    created_at: datetime = Field(..., description="Timestamp when the admin was created")
    updated_at: datetime = Field(..., description="Timestamp when the admin was last updated")

    model_config = ConfigDict(extra="forbid")

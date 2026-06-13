"""Response schemas for authentication-related APIs in the provider backend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ProviderAdminLoginOtpResponse(BaseModel):
    """Response payload returned after starting the provider-admin login flow.

    Attributes:
        message: Human-readable response message.
        email: Provider-admin email that received the OTP.
        otp_expires_at: Timestamp when the provider-admin OTP expires.
    """

    message: str = Field(..., description="Human-readable response message")
    email: EmailStr = Field(..., description="Provider-admin email that received the OTP")
    otp_expires_at: datetime = Field(
        ...,
        description="Timestamp when the provider-admin OTP expires",
    )


class ProviderAdminLoginVerifyResponse(BaseModel):
    """Response payload returned after successful provider-admin OTP verification.

    Attributes:
        message: Human-readable response message.
        access_token: JWT access token for the authenticated provider admin.
        token_type: Token type returned to the client.
        admin_id: Authenticated provider-admin identifier.
        email: Authenticated provider-admin email.
    """

    message: str = Field(..., description="Human-readable response message")
    access_token: str = Field(
        ...,
        description="JWT access token for the provider admin",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type returned to the client",
    )
    admin_id: str = Field(..., description="Authenticated provider-admin identifier")
    email: EmailStr = Field(..., description="Authenticated provider-admin email")

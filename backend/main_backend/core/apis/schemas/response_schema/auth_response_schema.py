"""Response schemas for authentication-related APIs in the main backend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AdminLoginOtpResponse(BaseModel):
    """Response payload returned after starting the admin login flow.

    Attributes:
        message: Human-readable response message.
        email: Admin email that received the OTP.
        otp_expires_at: Timestamp when the admin OTP expires.
    """

    message: str = Field(..., description="Human-readable response message")
    email: EmailStr = Field(..., description="Admin email that received the OTP")
    otp_expires_at: datetime = Field(..., description="Timestamp when the admin OTP expires")


class AdminLoginVerifyResponse(BaseModel):
    """Response payload returned after successful admin OTP verification.

    Attributes:
        message: Human-readable response message.
        access_token: JWT access token for the authenticated admin.
        token_type: Token type returned to the client.
        admin_id: Authenticated admin identifier.
        email: Authenticated admin email.
    """

    message: str = Field(..., description="Human-readable response message")
    access_token: str = Field(..., description="JWT access token for the admin")
    token_type: str = Field(default="bearer", description="Token type returned to the client")
    admin_id: str = Field(..., description="Authenticated admin identifier")
    email: EmailStr = Field(..., description="Authenticated admin email")

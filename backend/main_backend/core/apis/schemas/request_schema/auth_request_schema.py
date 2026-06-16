"""Request schemas for authentication-related APIs in the main backend.

This module is focused mainly on admin authentication because customer OTP
login requests are already covered in ``user_request_schema.py``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminLoginRequest(BaseModel):
    """Request payload for starting the admin login flow.

    Attributes:
        email: Admin email used as login identity.
        password: Plain-text admin password entered during login.
    """

    email: EmailStr = Field(..., description="Admin email used for login")
    password: str = Field(..., min_length=8, description="Plain-text admin password")

    model_config = ConfigDict(extra="forbid")


class AdminLoginVerifyRequest(BaseModel):
    """Request payload for verifying admin OTP after password validation.

    Attributes:
        email: Admin email receiving the OTP.
        otp: Plain OTP value entered by the admin.
    """

    email: EmailStr = Field(..., description="Admin email receiving the OTP")
    otp: str = Field(
        ...,
        min_length=4,
        max_length=8,
        description="Plain OTP value entered by the admin",
    )

    model_config = ConfigDict(extra="forbid")

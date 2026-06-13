"""Request schemas for authentication-related APIs in the provider backend.

This module is focused on provider-admin authentication. These users access the
provider admin frontend using email, password, and OTP.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProviderAdminLoginRequest(BaseModel):
    """Request payload for starting the provider-admin login flow.

    Attributes:
        email: Provider-admin email used as login identity.
        password: Plain-text provider-admin password entered during login.
    """

    email: EmailStr = Field(..., description="Provider-admin email used for login")
    password: str = Field(
        ...,
        min_length=8,
        description="Plain-text provider-admin password",
    )

    model_config = ConfigDict(extra="forbid")


class ProviderAdminLoginVerifyRequest(BaseModel):
    """Request payload for verifying provider-admin OTP after password validation.

    Attributes:
        email: Provider-admin email receiving the OTP.
        otp: Plain OTP value entered by the provider admin.
    """

    email: EmailStr = Field(..., description="Provider-admin email receiving the OTP")
    otp: str = Field(
        ...,
        min_length=4,
        max_length=8,
        description="Plain OTP value entered by the provider admin",
    )

    model_config = ConfigDict(extra="forbid")

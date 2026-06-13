"""Request schemas for user- and admin-related APIs in the main backend.

This module contains only request payloads. The schema set is aligned with the
current InsureFlow flow:

- customers do not complete a separate registration step before starting a
  journey
- customers may later request a login OTP using their mobile number
- customers may later verify that OTP to access status, resume flow, or policy
  documents
- admins are created and managed separately
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserAddressRequest(BaseModel):
    """Represents structured address information provided by a user.

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


class UserLoginOtpRequest(BaseModel):
    """Request payload for sending a login OTP to a customer's mobile number.

    This is used for returning customers who want to resume a journey, check
    transaction status, or access issued policy documents.

    Attributes:
        mobile_number: Customer mobile number used for OTP-based login.
    """

    mobile_number: str = Field(
        ...,
        min_length=10,
        description="Customer mobile number used for OTP-based login",
    )


class UserLoginVerifyRequest(BaseModel):
    """Request payload for verifying a customer's login OTP.

    Attributes:
        mobile_number: Customer mobile number receiving the OTP.
        otp: Plain OTP value entered by the customer.
    """

    mobile_number: str = Field(
        ...,
        min_length=10,
        description="Customer mobile number receiving the login OTP",
    )
    otp: str = Field(
        ...,
        min_length=4,
        max_length=8,
        description="Plain OTP value entered by the customer",
    )


class UserUpdateRequest(BaseModel):
    """Request payload for updating a customer's profile information.

    All fields are optional. Only provided fields should be updated.

    Attributes:
        first_name: Customer's given name.
        last_name: Customer's family name.
        dob: Customer's date of birth.
        address: Customer's updated residential address.
        user_metadata: Optional dictionary for additional user-related data.
    """

    first_name: str | None = Field(default=None, description="Customer's first name")
    last_name: str | None = Field(default=None, description="Customer's last name")
    dob: date | None = Field(
        default=None,
        description="Customer's date of birth in YYYY-MM-DD format",
    )
    address: UserAddressRequest | None = Field(
        default=None,
        description="Customer's updated residential address",
    )
    user_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata about the customer",
    )


class AdminCreateRequest(BaseModel):
    """Request payload for creating a new admin account.

    Attributes:
        first_name: Admin's given name.
        last_name: Admin's family name.
        email: Admin's unique email address used for login.
        password: Plain-text password that will be hashed before storage.
        mobile_number: Admin's contact mobile number.
    """

    first_name: str = Field(..., description="Admin's first name")
    last_name: str = Field(..., description="Admin's last name")
    email: EmailStr = Field(..., description="Admin email address used for login")
    password: str = Field(
        ...,
        min_length=8,
        description="Plain-text password that will be hashed before storage",
    )
    mobile_number: str = Field(..., min_length=10, description="Admin mobile number")


class AdminUpdateRequest(BaseModel):
    """Request payload for updating an admin's profile information.

    All fields are optional. Only provided fields should be updated.

    Attributes:
        first_name: Admin's given name.
        last_name: Admin's family name.
        mobile_number: Admin's contact mobile number.
    """

    first_name: str | None = Field(default=None, description="Admin's first name")
    last_name: str | None = Field(default=None, description="Admin's last name")
    mobile_number: str | None = Field(
        default=None,
        min_length=10,
        description="Admin's contact mobile number",
    )

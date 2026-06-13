"""Response schemas for company-related APIs in the provider backend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyResponse(BaseModel):
    """Represents one registered company returned by the provider backend.

    Attributes:
        company_name: Unique company name.
        company_type: Registered company type.
        contact_email: Optional company contact email.
        contact_phone: Optional company contact phone.
        is_active: Whether the company is active.
        created_at: Company creation timestamp.
        updated_at: Company last-update timestamp.
    """

    company_name: str = Field(..., description="Unique company name")
    company_type: str = Field(..., description="Registered company type")
    contact_email: str | None = Field(default=None, description="Optional company contact email")
    contact_phone: str | None = Field(default=None, description="Optional company contact phone")
    is_active: bool = Field(..., description="Whether the company is active")
    created_at: datetime = Field(..., description="Company creation timestamp")
    updated_at: datetime = Field(..., description="Company last-update timestamp")

    model_config = ConfigDict(extra="forbid")


class CompanyCreateResponse(BaseModel):
    """Response payload returned after registering a company.

    Attributes:
        message: Human-readable response message.
        company: Registered company details.
        plain_api_key: Plain API key returned one time during registration.
    """

    message: str = Field(..., description="Human-readable response message")
    company: CompanyResponse = Field(..., description="Registered company details")
    plain_api_key: str = Field(
        ...,
        description="Plain API key returned one time during registration",
    )

    model_config = ConfigDict(extra="forbid")


class CompanyListResponse(BaseModel):
    """Represents a list of registered companies.

    Attributes:
        items: List of returned company records.
        total_count: Total number of returned companies.
    """

    items: list[CompanyResponse] = Field(default_factory=list, description="List of companies")
    total_count: int = Field(..., ge=0, description="Total number of returned companies")

    model_config = ConfigDict(extra="forbid")

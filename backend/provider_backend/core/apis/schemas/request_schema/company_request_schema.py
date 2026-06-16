"""Request schemas for company-related APIs in the provider backend."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreateRequest(BaseModel):
    """Request payload for creating a provider or mediator company.

    Attributes:
        company_name: Unique company name to register.
        company_type: Registered company type such as provider or mediator.
        created_by_admin_id: Identifier of the provider admin creating the record.
        contact_person_name: Optional primary contact person for the company.
        contact_email: Optional company contact email.
        contact_phone: Optional company contact phone number.
    """

    company_name: str = Field(..., description="Unique company name to register")
    company_type: str = Field(
        ...,
        description='Registered company type such as "provider" or "mediator"',
    )
    created_by_admin_id: str = Field(
        ...,
        description="Identifier of the provider admin creating the record",
    )
    contact_person_name: str | None = Field(
        default=None,
        description="Optional primary contact person for the company",
    )
    contact_email: str | None = Field(
        default=None,
        description="Optional company contact email",
    )
    contact_phone: str | None = Field(
        default=None,
        description="Optional company contact phone number",
    )

    model_config = ConfigDict(extra="forbid")


class CompanyUpdateRequest(BaseModel):
    """Request payload for updating a registered company.

    Attributes:
        contact_person_name: Updated primary contact person for the company.
        contact_email: Updated company contact email.
        contact_phone: Updated company contact phone number.
        is_active: Updated active status of the company.
    """

    contact_person_name: str | None = Field(
        default=None,
        description="Updated primary contact person for the company",
    )
    contact_email: str | None = Field(
        default=None,
        description="Updated company contact email",
    )
    contact_phone: str | None = Field(
        default=None,
        description="Updated company contact phone number",
    )
    is_active: bool | None = Field(
        default=None,
        description="Updated active status of the company",
    )

    model_config = ConfigDict(extra="forbid")

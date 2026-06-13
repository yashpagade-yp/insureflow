"""Company models for the InsureFlow provider backend.

This module contains the provider-side company document model used to register
insurance provider companies and mediator companies for controlled API access.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from odmantic import Field, Model
from odmantic.config import ODMConfigDict


def generate_company_code() -> str:
    """Generate a unique business-facing company code."""

    return f"COM-{uuid4().hex[:10].upper()}"


class CompanyType(str, Enum):
    """Defines the supported company categories in provider backend.

    Attributes:
        PROVIDER: Insurance provider company offering plans.
        MEDIATOR: Mediator platform such as InsureFlow.
    """

    PROVIDER = "provider"
    MEDIATOR = "mediator"


class Company(Model):
    """Represents a registered company stored in the `companies` collection.

    The company model is used to onboard provider companies and the InsureFlow
    broker/mediator entry. In the current project flow, these company records
    are created and managed only by admin users in the provider backend.

    Attributes:
        company_code: Unique business-facing company code.
        company_name: Unique name of the registered company.
        company_type: Type of the registered company.
        created_by_admin_id: Identifier of the admin who created the record.
        contact_person_name: Optional primary contact person for the company.
        contact_email: Optional contact email for the company.
        contact_phone: Optional contact phone number for the company.
        api_key_hash: Hashed API key stored for secure communication.
        is_active: Whether the company is currently active.
        created_at: UTC timestamp when the company was created.
        updated_at: UTC timestamp when the company was last updated.
    """

    company_code: str = Field(
        default_factory=generate_company_code,
        unique=True,
        description="Unique business-facing code for the registered company",
    )
    company_name: str = Field(
        ...,
        unique=True,
        description="Unique name of the registered company",
    )
    company_type: CompanyType = Field(
        ...,
        description="Type of the registered company",
    )
    created_by_admin_id: str = Field(
        ...,
        description="Identifier of the admin who created this company record",
    )
    contact_person_name: str | None = Field(
        default=None,
        description="Optional primary contact person for the company",
    )
    contact_email: str | None = Field(
        default=None,
        description="Optional contact email for the company",
    )
    contact_phone: str | None = Field(
        default=None,
        description="Optional contact phone number for the company",
    )
    api_key_hash: str = Field(
        ...,
        description="Hashed API key stored for secure communication",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the company is currently active",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the company was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the company was last updated",
    )

    model_config = ODMConfigDict(
        collection="companies",
        extra="forbid",
    )


CompanyModel = Company

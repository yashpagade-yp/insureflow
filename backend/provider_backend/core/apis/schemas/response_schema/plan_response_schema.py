"""Response schemas for insurance-plan APIs in the provider backend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PlanAddOnResponse(BaseModel):
    """Represents one add-on returned in a plan response.

    Attributes:
        name: Add-on name.
        description: Add-on description.
        price: Add-on price.
    """

    name: str = Field(..., description="Add-on name")
    description: str = Field(..., description="Add-on description")
    price: float = Field(..., ge=0, description="Add-on price")


class PlanResponse(BaseModel):
    """Represents one provider insurance plan returned by the provider backend.

    Attributes:
        company_name: Provider company name.
        logo_url: Optional provider logo URL.
        plan_name: Business name of the insurance plan.
        plan_code: Unique provider-side plan code.
        insurance_type: Insurance category.
        coverage_amount: Coverage amount.
        base_premium: Base premium.
        duration_years: Plan duration in years.
        benefits: Plan benefits.
        terms: Optional plan terms.
        available_add_ons: Available add-ons for the plan.
        created_at: Plan creation timestamp.
        updated_at: Plan last-update timestamp.
    """

    company_name: str = Field(..., description="Provider company name")
    logo_url: str | None = Field(default=None, description="Optional provider logo URL")
    plan_name: str = Field(..., description="Business name of the insurance plan")
    plan_code: str = Field(..., description="Unique provider-side plan code")
    insurance_type: str = Field(..., description="Insurance category")
    coverage_amount: float = Field(..., ge=0, description="Coverage amount")
    base_premium: float = Field(..., ge=0, description="Base premium")
    duration_years: int = Field(..., ge=1, description="Plan duration in years")
    benefits: list[str] = Field(default_factory=list, description="Plan benefits")
    terms: str | None = Field(default=None, description="Optional plan terms")
    available_add_ons: list[PlanAddOnResponse] = Field(
        default_factory=list,
        description="Available add-ons for the plan",
    )
    created_at: datetime = Field(..., description="Plan creation timestamp")
    updated_at: datetime = Field(..., description="Plan last-update timestamp")


class PlanListResponse(BaseModel):
    """Represents a list of provider insurance plans.

    Attributes:
        items: List of returned plan records.
        total_count: Total number of returned plans.
    """

    items: list[PlanResponse] = Field(default_factory=list, description="List of plans")
    total_count: int = Field(..., ge=0, description="Total number of returned plans")

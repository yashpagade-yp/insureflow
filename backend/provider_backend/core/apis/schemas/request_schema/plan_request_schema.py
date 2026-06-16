"""Request schemas for insurance-plan APIs in the provider backend."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PlanAddOnRequest(BaseModel):
    """Represents one add-on included in a plan create/update request.

    Attributes:
        name: Add-on name.
        description: Add-on description.
        price: Add-on price.
    """

    name: str = Field(..., description="Add-on name")
    description: str = Field(..., description="Add-on description")
    price: float = Field(..., ge=0, description="Add-on price")

    model_config = ConfigDict(extra="forbid")


class PlanCreateRequest(BaseModel):
    """Request payload for creating a provider insurance plan.

    Attributes:
        company_name: Provider company name.
        logo_url: Optional provider logo URL.
        plan_name: Business name of the insurance plan.
        plan_code: Unique provider-side plan code.
        insurance_type: Insurance category such as life or health.
        coverage_amount: Coverage amount for the plan.
        base_premium: Base premium for the plan.
        duration_years: Plan duration in years.
        benefits: Plan benefits.
        terms: Optional plan terms.
        available_add_ons: Available add-ons for the plan.
    """

    company_name: str = Field(..., description="Provider company name")
    logo_url: str | None = Field(default=None, description="Optional provider logo URL")
    plan_name: str = Field(..., description="Business name of the insurance plan")
    plan_code: str = Field(..., description="Unique provider-side plan code")
    insurance_type: str = Field(..., description='Insurance category such as "life" or "health"')
    coverage_amount: float = Field(..., ge=0, description="Coverage amount for the plan")
    base_premium: float = Field(..., ge=0, description="Base premium for the plan")
    duration_years: int = Field(..., ge=1, description="Plan duration in years")
    benefits: list[str] = Field(default_factory=list, description="Plan benefits")
    terms: str | None = Field(default=None, description="Optional plan terms")
    available_add_ons: list[PlanAddOnRequest] = Field(
        default_factory=list,
        description="Available add-ons for the plan",
    )

    model_config = ConfigDict(extra="forbid")


class PlanUpdateRequest(BaseModel):
    """Request payload for updating a provider insurance plan.

    Attributes:
        logo_url: Updated provider logo URL.
        plan_name: Updated plan name.
        insurance_type: Updated insurance category.
        coverage_amount: Updated coverage amount.
        base_premium: Updated base premium.
        duration_years: Updated plan duration.
        benefits: Updated plan benefits.
        terms: Updated plan terms.
        available_add_ons: Updated available add-ons.
    """

    logo_url: str | None = Field(default=None, description="Updated provider logo URL")
    plan_name: str | None = Field(default=None, description="Updated plan name")
    insurance_type: str | None = Field(default=None, description="Updated insurance category")
    coverage_amount: float | None = Field(default=None, ge=0, description="Updated coverage amount")
    base_premium: float | None = Field(default=None, ge=0, description="Updated base premium")
    duration_years: int | None = Field(default=None, ge=1, description="Updated plan duration")
    benefits: list[str] | None = Field(default=None, description="Updated plan benefits")
    terms: str | None = Field(default=None, description="Updated plan terms")
    available_add_ons: list[PlanAddOnRequest] | None = Field(
        default=None,
        description="Updated available add-ons",
    )

    model_config = ConfigDict(extra="forbid")

"""Insurance plan models for the InsureFlow provider backend.

This module contains the provider-side insurance plan document model and the
embedded add-on model stored inside each plan. The structure follows the
current project specification and the ODMantic-based project pattern.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from odmantic import Field, Model
from odmantic.config import ODMConfigDict
from pydantic import BaseModel


class InsuranceType(str, Enum):
    """Defines the supported insurance categories for provider plans.

    Attributes:
        LIFE: Life insurance plans.
        HEALTH: Health insurance plans.
        GENERAL: General insurance plans.
    """

    LIFE = "life"
    HEALTH = "health"
    GENERAL = "general"


class EmbeddedAddOn(BaseModel):
    """Represents an add-on embedded inside an insurance plan.

    Attributes:
        name: Add-on name.
        description: Short explanation of the add-on.
        price: Additional yearly premium for the add-on.
    """

    name: str = Field(..., description="Name of the insurance add-on")
    description: str = Field(..., description="Description of the insurance add-on")
    price: float = Field(..., ge=0, description="Additional yearly premium for the add-on")


class InsurancePlan(Model):
    """Represents an insurance plan stored in the `insurance_plans` collection.

    Each plan belongs to a provider company and can optionally include embedded
    add-ons that are available for quote generation and selection.

    Attributes:
        company_name: Name of the provider company offering the plan.
        logo_url: Optional logo URL for the provider company.
        plan_name: Business name of the insurance plan.
        plan_code: Unique provider-side code for the plan.
        insurance_type: Category of insurance offered by the plan.
        coverage_amount: Coverage amount associated with the plan.
        base_premium: Base yearly premium for the plan.
        duration_years: Duration of coverage in years.
        benefits: List of key benefits included in the plan.
        terms: Optional textual terms or summary of plan conditions.
        available_add_ons: Embedded list of add-ons available for the plan.
        created_at: UTC timestamp when the plan was created.
        updated_at: UTC timestamp when the plan was last updated.
    """

    company_name: str = Field(..., description="Name of the provider company")
    logo_url: Optional[str] = Field(
        default=None,
        description="Optional logo URL for the provider company",
    )
    plan_name: str = Field(..., description="Business name of the insurance plan")
    plan_code: str = Field(
        ...,
        unique=True,
        description="Unique provider-side code for the insurance plan",
    )
    insurance_type: InsuranceType = Field(
        ...,
        description="Insurance category for the plan",
    )
    coverage_amount: float = Field(..., ge=0, description="Coverage amount for the plan")
    base_premium: float = Field(..., ge=0, description="Base yearly premium for the plan")
    duration_years: int = Field(..., ge=1, description="Plan duration in years")
    benefits: List[str] = Field(
        default_factory=list,
        description="List of benefits included in the insurance plan",
    )
    terms: Optional[str] = Field(
        default=None,
        description="Optional textual terms for the plan",
    )
    available_add_ons: List[EmbeddedAddOn] = Field(
        default_factory=list,
        description="Embedded list of add-ons available for this plan",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the insurance plan was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the insurance plan was last updated",
    )

    model_config = ODMConfigDict(
        collection="insurance_plans",
        extra="forbid",
    )


InsuranceModel = InsurancePlan

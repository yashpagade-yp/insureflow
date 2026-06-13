"""Insurance detail models for the InsureFlow main backend.

This module contains the customer-side insurance detail document model used to
store one transaction-specific form snapshot. The model supports resume flow by
keeping the latest form step and completion state in the main backend.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any

from odmantic import Field, Model
from odmantic.config import ODMConfigDict


class InsuranceType(str, Enum):
    """Defines the supported insurance categories for customer journeys.

    Attributes:
        LIFE: Life insurance journey.
        HEALTH: Health insurance journey.
        GENERAL: General insurance journey.
    """

    LIFE = "life"
    HEALTH = "health"
    GENERAL = "general"


class InsuranceDetail(Model):
    """Represents a transaction-specific insurance form snapshot.

    This model belongs in the main backend because it stores the customer-side
    application data collected before quote generation and purchase. One user
    can have multiple insurance detail documents across different transaction
    journeys.

    Attributes:
        transaction_id: Identifier of the related transaction.
        user_id: Identifier of the user who owns the journey.
        insurance_type: Insurance category for the current form.
        proposer_first_name: Customer first name for the current journey.
        proposer_last_name: Customer last name for the current journey.
        proposer_mobile_number: Customer mobile number used in the form.
        proposer_email: Optional customer email used in the form.
        proposer_dob: Optional customer date of birth.
        proposer_gender: Optional customer gender value.
        insured_members: Flexible list of insured-member details.
        sum_insured_requested: Requested coverage amount.
        policy_term_years: Requested policy term in years.
        premium_preference: Optional premium preference for the journey.
        occupation: Optional occupation used for eligibility or pricing.
        annual_income: Optional annual income used for eligibility checks.
        city: Optional city used in the form.
        state: Optional state used in the form.
        postal_code: Optional postal code used in the form.
        existing_insurance_details: Optional existing-insurance snapshot.
        medical_history: Optional medical history details.
        additional_answers: Optional flexible answers for product-specific
            questions.
        form_step: Latest saved form step for resume flow.
        is_form_completed: Whether the insurance-detail form is complete.
        created_at: UTC timestamp when the insurance detail was created.
        updated_at: UTC timestamp when the insurance detail was last updated.
    """

    transaction_id: str = Field(
        ...,
        description="Identifier of the related transaction",
    )
    user_id: str = Field(..., description="Identifier of the user who owns the journey")
    insurance_type: InsuranceType = Field(
        ...,
        description="Insurance category for the current customer journey",
    )

    proposer_first_name: str | None = Field(
        default=None,
        description="Customer first name for the current journey",
    )
    proposer_last_name: str | None = Field(
        default=None,
        description="Customer last name for the current journey",
    )
    proposer_mobile_number: str | None = Field(
        default=None,
        description="Customer mobile number captured in the form",
    )
    proposer_email: str | None = Field(
        default=None,
        description="Optional customer email captured in the form",
    )
    proposer_dob: date | None = Field(
        default=None,
        description="Optional customer date of birth",
    )
    proposer_gender: str | None = Field(
        default=None,
        description="Optional customer gender value",
    )

    insured_members: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Flexible list of insured-member details for the journey",
    )
    sum_insured_requested: float | None = Field(
        default=None,
        ge=0,
        description="Requested coverage amount for the journey",
    )
    policy_term_years: int | None = Field(
        default=None,
        ge=1,
        description="Requested policy term in years",
    )
    premium_preference: str | None = Field(
        default=None,
        description="Optional premium preference for the journey",
    )

    occupation: str | None = Field(
        default=None,
        description="Optional occupation used for eligibility or pricing",
    )
    annual_income: float | None = Field(
        default=None,
        ge=0,
        description="Optional annual income used for eligibility checks",
    )
    city: str | None = Field(default=None, description="Optional city used in the form")
    state: str | None = Field(default=None, description="Optional state used in the form")
    postal_code: str | None = Field(
        default=None,
        description="Optional postal code used in the form",
    )

    existing_insurance_details: dict[str, Any] | None = Field(
        default=None,
        description="Optional snapshot of existing insurance details",
    )
    medical_history: dict[str, Any] | None = Field(
        default=None,
        description="Optional medical history details for the journey",
    )
    additional_answers: dict[str, Any] | None = Field(
        default=None,
        description="Optional flexible answers for product-specific questions",
    )

    form_step: str | None = Field(
        default=None,
        description="Latest saved form step for resume flow",
    )
    is_form_completed: bool = Field(
        default=False,
        description="Whether the insurance-detail form is complete",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the insurance detail was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the insurance detail was last updated",
    )

    model_config = ODMConfigDict(
        collection="insurance_details",
        extra="forbid",
    )


InsuranceDetailModel = InsuranceDetail

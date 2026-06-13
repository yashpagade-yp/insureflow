"""Request schemas for insurance-detail APIs in the main backend.

These schemas are aligned with the real first customer flow in InsureFlow:

- the customer directly fills the insurance form
- the form creates or updates a transaction-linked InsuranceDetail
- the same form progress can later be resumed
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ....models.insurance_detail_model import InsuranceType


class InsuranceDetailCreateRequest(BaseModel):
    """Request payload for starting a new insurance-detail journey.

    Attributes:
        mobile_number: Customer mobile number used as identity.
        insurance_type: Insurance category for the current journey.
        proposer_first_name: Customer first name.
        proposer_last_name: Customer last name.
        proposer_email: Optional customer email.
        proposer_dob: Optional customer date of birth.
        proposer_gender: Optional customer gender value.
        insured_members: Flexible list of insured-member details.
        sum_insured_requested: Requested coverage amount.
        policy_term_years: Requested policy term in years.
        premium_preference: Optional premium preference.
        occupation: Optional occupation used for quote logic.
        annual_income: Optional annual income used for quote logic.
        city: Optional city used in the form.
        state: Optional state used in the form.
        postal_code: Optional postal code used in the form.
        existing_insurance_details: Optional existing-insurance snapshot.
        medical_history: Optional medical history details.
        additional_answers: Optional product-specific answers.
        form_step: Latest saved form step.
        is_form_completed: Whether the form is complete.
    """

    mobile_number: str = Field(..., min_length=10, description="Customer mobile number")
    insurance_type: InsuranceType = Field(..., description="Insurance category for the current journey")
    proposer_first_name: str | None = Field(default=None, description="Customer first name")
    proposer_last_name: str | None = Field(default=None, description="Customer last name")
    proposer_email: str | None = Field(default=None, description="Optional customer email")
    proposer_dob: date | None = Field(default=None, description="Optional customer date of birth")
    proposer_gender: str | None = Field(default=None, description="Optional customer gender value")
    insured_members: list[dict[str, Any]] = Field(default_factory=list, description="Flexible list of insured-member details")
    sum_insured_requested: float | None = Field(default=None, ge=0, description="Requested coverage amount")
    policy_term_years: int | None = Field(default=None, ge=1, description="Requested policy term in years")
    premium_preference: str | None = Field(default=None, description="Optional premium preference")
    occupation: str | None = Field(default=None, description="Optional occupation used for quote logic")
    annual_income: float | None = Field(default=None, ge=0, description="Optional annual income used for quote logic")
    city: str | None = Field(default=None, description="Optional city used in the form")
    state: str | None = Field(default=None, description="Optional state used in the form")
    postal_code: str | None = Field(default=None, description="Optional postal code used in the form")
    existing_insurance_details: dict[str, Any] | None = Field(default=None, description="Optional existing-insurance snapshot")
    medical_history: dict[str, Any] | None = Field(default=None, description="Optional medical history details")
    additional_answers: dict[str, Any] | None = Field(default=None, description="Optional product-specific answers")
    form_step: str | None = Field(default=None, description="Latest saved form step")
    is_form_completed: bool = Field(default=False, description="Whether the form is complete")

    model_config = ConfigDict(extra="forbid")


class InsuranceDetailUpdateRequest(BaseModel):
    """Request payload for updating a transaction-linked insurance detail.

    All fields are optional. Only provided fields should be updated.

    Attributes:
        proposer_first_name: Updated customer first name.
        proposer_last_name: Updated customer last name.
        proposer_mobile_number: Updated customer mobile number.
        proposer_email: Updated customer email.
        proposer_dob: Updated customer date of birth.
        proposer_gender: Updated customer gender value.
        insured_members: Updated insured-member list.
        sum_insured_requested: Updated requested coverage amount.
        policy_term_years: Updated policy term in years.
        premium_preference: Updated premium preference.
        occupation: Updated occupation.
        annual_income: Updated annual income.
        city: Updated city value.
        state: Updated state value.
        postal_code: Updated postal code value.
        existing_insurance_details: Updated existing-insurance snapshot.
        medical_history: Updated medical history details.
        additional_answers: Updated product-specific answers.
        form_step: Updated latest saved form step.
        is_form_completed: Updated completion flag.
    """

    proposer_first_name: str | None = Field(default=None, description="Updated customer first name")
    proposer_last_name: str | None = Field(default=None, description="Updated customer last name")
    proposer_mobile_number: str | None = Field(default=None, description="Updated customer mobile number")
    proposer_email: str | None = Field(default=None, description="Updated customer email")
    proposer_dob: date | None = Field(default=None, description="Updated customer date of birth")
    proposer_gender: str | None = Field(default=None, description="Updated customer gender value")
    insured_members: list[dict[str, Any]] | None = Field(default=None, description="Updated insured-member list")
    sum_insured_requested: float | None = Field(default=None, ge=0)
    policy_term_years: int | None = Field(default=None, ge=1)
    premium_preference: str | None = Field(default=None, description="Updated premium preference")
    occupation: str | None = Field(default=None, description="Updated occupation")
    annual_income: float | None = Field(default=None, ge=0)
    city: str | None = Field(default=None, description="Updated city value")
    state: str | None = Field(default=None, description="Updated state value")
    postal_code: str | None = Field(default=None, description="Updated postal code value")
    existing_insurance_details: dict[str, Any] | None = Field(default=None, description="Updated existing-insurance snapshot")
    medical_history: dict[str, Any] | None = Field(default=None, description="Updated medical history details")
    additional_answers: dict[str, Any] | None = Field(default=None, description="Updated product-specific answers")
    form_step: str | None = Field(default=None, description="Updated latest saved form step")
    is_form_completed: bool | None = Field(default=None, description="Updated completion flag")

    model_config = ConfigDict(extra="forbid")

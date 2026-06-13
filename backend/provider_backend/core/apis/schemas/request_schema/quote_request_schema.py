"""Request schemas for quote-generation APIs in the provider backend."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QuoteGenerationRequest(BaseModel):
    """Request payload received from the main backend to generate quotes.

    Attributes:
        transaction_id: Transaction identifier for the journey.
        user_id: User identifier linked to the journey.
        insurance_type: Insurance category for the journey.
        proposer_dob: Optional proposer date of birth.
        proposer_gender: Optional proposer gender.
        city: Optional city used for quote logic.
        state: Optional state used for quote logic.
        sum_insured_requested: Requested coverage amount.
        policy_term_years: Requested policy term.
        occupation: Optional occupation for quote rules.
        annual_income: Optional annual income.
        medical_history: Optional medical history details.
        additional_answers: Optional product-specific answers.
    """

    transaction_id: str = Field(..., description="Transaction identifier for the journey")
    user_id: str = Field(..., description="User identifier linked to the journey")
    insurance_type: str = Field(..., description="Insurance category for the journey")
    proposer_dob: str | None = Field(default=None, description="Optional proposer date of birth")
    proposer_gender: str | None = Field(default=None, description="Optional proposer gender")
    city: str | None = Field(default=None, description="Optional city used for quote logic")
    state: str | None = Field(default=None, description="Optional state used for quote logic")
    sum_insured_requested: float | None = Field(default=None, ge=0, description="Requested coverage amount")
    policy_term_years: int | None = Field(default=None, ge=1, description="Requested policy term")
    occupation: str | None = Field(default=None, description="Optional occupation for quote rules")
    annual_income: float | None = Field(default=None, ge=0, description="Optional annual income")
    medical_history: dict | None = Field(default=None, description="Optional medical history details")
    additional_answers: dict | None = Field(default=None, description="Optional product-specific answers")

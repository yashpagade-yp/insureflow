"""Request schemas for customer quote-selection APIs in the main backend."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QuoteSelectPlanRequest(BaseModel):
    """Request payload for selecting one quote/plan for a transaction.

    Attributes:
        transaction_id: Transaction identifier for the journey.
        selected_plan_id: Provider plan identifier chosen by the customer.
    """

    transaction_id: str = Field(..., description="Transaction identifier for the journey")
    selected_plan_id: str = Field(
        ...,
        description="Provider plan identifier chosen by the customer",
    )

    model_config = ConfigDict(extra="forbid")


class QuoteSelectedAddOnRequest(BaseModel):
    """Represents one selected add-on in a quote-selection request.

    Attributes:
        name: Add-on name selected by the customer.
        price: Add-on price selected by the customer.
    """

    name: str = Field(..., description="Selected add-on name")
    price: float = Field(..., ge=0, description="Selected add-on price")

    model_config = ConfigDict(extra="forbid")


class QuoteSelectAddOnsRequest(BaseModel):
    """Request payload for saving selected add-ons for a chosen plan.

    Attributes:
        transaction_id: Transaction identifier for the journey.
        selected_plan_id: Provider plan identifier chosen by the customer.
        selected_add_ons: List of selected add-ons for the chosen plan.
    """

    transaction_id: str = Field(..., description="Transaction identifier for the journey")
    selected_plan_id: str = Field(
        ...,
        description="Provider plan identifier chosen by the customer",
    )
    selected_add_ons: list[QuoteSelectedAddOnRequest] = Field(
        default_factory=list,
        description="Selected add-ons for the chosen plan",
    )

    model_config = ConfigDict(extra="forbid")

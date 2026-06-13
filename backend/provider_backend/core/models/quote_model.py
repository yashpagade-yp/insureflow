"""Quote models for the InsureFlow provider backend.

This module contains the provider-side quote document model together with the
embedded quote item and selected add-on structures. The quote model stores one
document per transaction, containing all matching plan quote items.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from odmantic.config import ODMConfigDict
from pydantic import BaseModel


class QuoteStatus(str, Enum):
    """Defines the supported states for an individual quote item.

    Attributes:
        GENERATED: Quote item has been generated.
        SELECTED: Quote item has been selected by the user.
        CONFIRMED: Quote item has been confirmed.
    """

    GENERATED = "GENERATED"
    SELECTED = "SELECTED"
    CONFIRMED = "CONFIRMED"


class SelectedAddOn(BaseModel):
    """Represents an add-on selected within a quote item.

    Attributes:
        name: Name of the selected add-on.
        price: Price of the selected add-on.
    """

    name: str = Field(..., description="Name of the selected add-on")
    price: float = Field(..., ge=0, description="Price of the selected add-on")


class AvailableAddOn(BaseModel):
    """Represents an add-on available for selection within a quote item.

    Attributes:
        name: Name of the available add-on.
        description: Short explanation of the available add-on.
        price: Price of the available add-on.
    """

    name: str = Field(..., description="Name of the available add-on")
    description: str = Field(..., description="Description of the available add-on")
    price: float = Field(..., ge=0, description="Price of the available add-on")


class QuoteItem(BaseModel):
    """Represents one plan quote embedded inside the transaction quote document.

    Attributes:
        plan_id: Identifier of the source insurance plan.
        company_name: Name of the provider company.
        logo_url: Optional logo URL for display purposes.
        plan_name: Name of the quoted insurance plan.
        coverage_amount: Coverage amount associated with the plan.
        base_premium: Base premium before add-ons and tax.
        duration_years: Duration of the quoted plan in years.
        benefits: List of benefits included in the quoted plan.
        available_add_ons: Embedded list of add-ons available for selection.
        selected_add_ons: Embedded list of selected add-ons.
        add_on_total: Total premium amount added by add-ons.
        tax_amount: Tax amount applied to the quote.
        total_premium: Final total premium for the quote item.
        quote_status: Current status of the quote item.
    """

    plan_id: str = Field(..., description="Identifier of the source insurance plan")
    company_name: str = Field(..., description="Name of the provider company")
    logo_url: str | None = Field(
        default=None,
        description="Optional logo URL for the provider company",
    )
    plan_name: str = Field(..., description="Name of the quoted insurance plan")
    coverage_amount: float = Field(..., ge=0, description="Coverage amount of the quoted plan")
    base_premium: float = Field(..., ge=0, description="Base premium of the quoted plan")
    duration_years: int = Field(..., ge=1, description="Duration of the quoted plan in years")
    benefits: list[str] = Field(
        default_factory=list,
        description="List of benefits included in the quoted plan",
    )
    available_add_ons: list[AvailableAddOn] = Field(
        default_factory=list,
        description="Embedded list of add-ons available for this quote item",
    )
    selected_add_ons: list[SelectedAddOn] = Field(
        default_factory=list,
        description="Embedded list of selected add-ons for this quote item",
    )
    add_on_total: float = Field(
        default=0.0,
        ge=0,
        description="Total premium amount added by selected add-ons",
    )
    tax_amount: float = Field(
        default=0.0,
        ge=0,
        description="Tax amount applied to the quote item",
    )
    total_premium: float = Field(..., ge=0, description="Final total premium for the quote item")
    quote_status: QuoteStatus = Field(
        default=QuoteStatus.GENERATED,
        description="Current status of the quote item",
    )


class Quote(Model):
    """Represents a quote document stored in the `quotes` collection.

    One quote document is created per transaction and stores all matching plan
    quotes inside the embedded `items` list.

    Attributes:
        transaction_id: Identifier of the related transaction from main backend.
        selected_plan_id: Optional selected provider plan identifier for the
            transaction.
        items: Embedded list of generated quote items for the transaction.
        created_at: UTC timestamp when the quote document was created.
        updated_at: UTC timestamp when the quote document was last updated.
    """

    transaction_id: str = Field(
        ...,
        description="Identifier of the related main-backend transaction",
    )
    selected_plan_id: str | None = Field(
        default=None,
        description="Optional selected provider plan identifier for the transaction",
    )
    items: list[QuoteItem] = Field(
        default_factory=list,
        description="Embedded list of quote items generated for the transaction",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the quote document was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the quote document was last updated",
    )

    model_config = ODMConfigDict(
        collection="quotes",
        extra="forbid",
    )


QuoteModel = Quote

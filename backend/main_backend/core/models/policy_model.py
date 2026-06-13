"""Policy models for the InsureFlow main backend.

This module contains the issued policy document model and the embedded add-on
snapshot model stored with the policy. The structure follows the current
project specification and the ODMantic-based project pattern.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from uuid import uuid4

from odmantic import Field, Model
from odmantic.config import ODMConfigDict
from pydantic import BaseModel


def generate_policy_number() -> str:
    """Generate a unique business-facing policy number."""

    return f"POL-{uuid4().hex[:12].upper()}"


class PolicyStatus(str, Enum):
    """Defines the supported states for an issued policy.

    Attributes:
        ACTIVE: Policy is currently active.
        EXPIRED: Policy has reached its end date.
        CANCELLED: Policy has been cancelled.
    """

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class PolicyAddOn(BaseModel):
    """Represents an embedded add-on snapshot on an issued policy.

    Attributes:
        name: Add-on name stored on the issued policy.
        price: Add-on price stored on the issued policy.
    """

    name: str = Field(..., description="Name of the policy add-on")
    price: float = Field(..., ge=0, description="Price of the policy add-on")


class Policy(Model):
    """Represents an issued policy document stored in the `policies` collection.

    The policy keeps both the `transaction_id` for backend traceability and the
    `policy_number` as the business-facing policy identifier.

    Attributes:
        policy_number: Unique business-facing policy reference.
        transaction_id: Identifier of the transaction that produced this policy.
        user_id: Identifier of the user who owns the policy.
        company_name: Name of the issuing insurance company.
        plan_name: Name of the selected insurance plan.
        coverage_amount: Coverage amount for the issued policy.
        base_premium: Base premium before add-ons and tax.
        add_ons: Embedded list of issued policy add-on snapshots.
        add_on_total: Total price of the selected add-ons.
        tax_amount: Tax amount applied to the policy premium.
        total_premium: Final premium paid for the policy.
        start_date: Policy start date.
        end_date: Policy expiry date.
        payment_reference: Optional payment reference linked to the issued
            policy.
        pdf_url: Optional URL for the generated policy PDF.
        policy_status: Current policy status.
        issued_at: UTC timestamp when the policy was issued.
        created_at: UTC timestamp when the policy was created.
    """

    policy_number: str = Field(
        default_factory=generate_policy_number,
        unique=True,
        description="Unique business-facing policy number",
    )
    transaction_id: str = Field(
        ...,
        description="Transaction identifier linked to this policy",
    )
    user_id: str = Field(..., description="Identifier of the user who owns the policy")
    company_name: str = Field(..., description="Name of the issuing insurance company")
    plan_name: str = Field(..., description="Name of the selected insurance plan")
    coverage_amount: float = Field(..., ge=0, description="Coverage amount for the policy")
    base_premium: float = Field(..., ge=0, description="Base premium for the policy")
    add_ons: list[PolicyAddOn] = Field(
        default_factory=list,
        description="Embedded list of add-on snapshots on the issued policy",
    )
    add_on_total: float = Field(
        default=0.0,
        ge=0,
        description="Total premium amount contributed by selected add-ons",
    )
    tax_amount: float = Field(..., ge=0, description="Tax amount applied to the policy")
    total_premium: float = Field(..., ge=0, description="Final total premium for the policy")
    start_date: date = Field(..., description="Policy start date")
    end_date: date = Field(..., description="Policy end date")
    payment_reference: str | None = Field(
        default=None,
        description="Optional payment reference linked to the issued policy",
    )
    pdf_url: str | None = Field(
        default=None,
        description="Optional generated PDF URL for the issued policy",
    )
    policy_status: PolicyStatus = Field(
        default=PolicyStatus.ACTIVE,
        description="Current status of the issued policy",
    )
    issued_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the policy was issued",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the policy was created",
    )

    model_config = ODMConfigDict(
        collection="policies",
        extra="forbid",
    )


PolicyModel = Policy

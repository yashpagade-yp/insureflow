"""Response schemas for policy-related APIs in the main backend."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PolicyAddOnResponse(BaseModel):
    """Represents one add-on returned in a policy response.

    Attributes:
        name: Policy add-on name.
        price: Policy add-on price.
    """

    name: str = Field(..., description="Policy add-on name")
    price: float = Field(..., ge=0, description="Policy add-on price")

    model_config = ConfigDict(extra="forbid")


class PolicyResponse(BaseModel):
    """Represents one issued policy returned by the main backend.

    Attributes:
        policy_number: Business-facing policy number.
        transaction_id: Transaction identifier linked to the policy.
        user_id: User identifier linked to the policy.
        company_name: Issuing insurance company name.
        plan_name: Issued insurance plan name.
        coverage_amount: Coverage amount of the policy.
        base_premium: Base premium of the policy.
        add_ons: Issued add-ons stored on the policy.
        add_on_total: Total add-on amount.
        tax_amount: Tax amount applied to the policy.
        total_premium: Final total premium paid.
        start_date: Policy start date.
        end_date: Policy end date.
        payment_reference: Optional payment reference linked to the policy.
        pdf_url: Optional generated policy PDF URL.
        policy_status: Current policy status.
        issued_at: Policy issuance timestamp.
        created_at: Policy creation timestamp.
    """

    policy_number: str = Field(..., description="Business-facing policy number")
    transaction_id: str = Field(..., description="Transaction identifier linked to the policy")
    user_id: str = Field(..., description="User identifier linked to the policy")
    company_name: str = Field(..., description="Issuing insurance company name")
    plan_name: str = Field(..., description="Issued insurance plan name")
    coverage_amount: float = Field(..., ge=0, description="Coverage amount of the policy")
    base_premium: float = Field(..., ge=0, description="Base premium of the policy")
    add_ons: list[PolicyAddOnResponse] = Field(
        default_factory=list,
        description="Issued add-ons stored on the policy",
    )
    add_on_total: float = Field(..., ge=0, description="Total add-on amount")
    tax_amount: float = Field(..., ge=0, description="Tax amount applied to the policy")
    total_premium: float = Field(..., ge=0, description="Final total premium paid")
    start_date: date = Field(..., description="Policy start date")
    end_date: date = Field(..., description="Policy end date")
    payment_reference: str | None = Field(
        default=None,
        description="Optional payment reference linked to the policy",
    )
    pdf_url: str | None = Field(default=None, description="Generated policy PDF URL")
    policy_status: str = Field(..., description="Current policy status")
    issued_at: datetime = Field(..., description="Policy issuance timestamp")
    created_at: datetime = Field(..., description="Policy creation timestamp")

    model_config = ConfigDict(extra="forbid")


class PolicyPdfResponse(BaseModel):
    """Represents policy PDF access details returned to the client.

    Attributes:
        policy_number: Business-facing policy number.
        pdf_url: Generated policy PDF URL.
        policy_status: Current policy status.
    """

    policy_number: str = Field(..., description="Business-facing policy number")
    pdf_url: str = Field(..., description="Generated policy PDF URL")
    policy_status: str = Field(..., description="Current policy status")

    model_config = ConfigDict(extra="forbid")


class PolicyListResponse(BaseModel):
    """Represents a list of issued policies for a user.

    Attributes:
        items: List of returned policy records.
        total_count: Total number of returned policies.
    """

    items: list[PolicyResponse] = Field(default_factory=list, description="List of policies")
    total_count: int = Field(..., ge=0, description="Total number of returned policies")

    model_config = ConfigDict(extra="forbid")

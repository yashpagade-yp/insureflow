"""Request schemas for policy-related APIs in the main backend."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PolicyIssueAddOnRequest(BaseModel):
    """Represents one add-on snapshot included during policy issuance.

    Attributes:
        name: Add-on name selected for the issued policy.
        price: Add-on price stored on the issued policy.
    """

    name: str = Field(..., description="Add-on name selected for the policy")
    price: float = Field(..., ge=0, description="Add-on price stored on the policy")

    model_config = ConfigDict(extra="forbid")


class PolicyIssueRequest(BaseModel):
    """Request payload for issuing a new policy from a completed transaction.

    Attributes:
        transaction_id: Transaction identifier linked to the policy.
        user_id: User identifier who owns the policy.
        company_name: Issuing insurance company name.
        plan_name: Selected insurance plan name.
        coverage_amount: Coverage amount for the policy.
        base_premium: Base premium before add-ons and tax.
        add_ons: Selected add-ons stored on the issued policy.
        add_on_total: Total amount contributed by selected add-ons.
        tax_amount: Tax amount applied to the policy premium.
        total_premium: Final premium paid for the policy.
        payment_reference: Payment reference linked to the policy.
        pdf_url: Optional generated policy PDF URL at issuance time.
        duration_years: Policy duration in years.
    """

    transaction_id: str = Field(..., description="Transaction identifier linked to the policy")
    user_id: str = Field(..., description="User identifier who owns the policy")
    company_name: str = Field(..., description="Issuing insurance company name")
    plan_name: str = Field(..., description="Selected insurance plan name")
    coverage_amount: float = Field(..., ge=0, description="Coverage amount for the policy")
    base_premium: float = Field(..., ge=0, description="Base premium before add-ons and tax")
    add_ons: list[PolicyIssueAddOnRequest] = Field(
        default_factory=list,
        description="Selected add-ons stored on the issued policy",
    )
    add_on_total: float = Field(..., ge=0, description="Total amount contributed by selected add-ons")
    tax_amount: float = Field(..., ge=0, description="Tax amount applied to the policy premium")
    total_premium: float = Field(..., ge=0, description="Final premium paid for the policy")
    payment_reference: str = Field(..., description="Payment reference linked to the policy")
    pdf_url: str | None = Field(default=None, description="Optional generated policy PDF URL")
    duration_years: int = Field(default=1, ge=1, description="Policy duration in years")

    model_config = ConfigDict(extra="forbid")


class PolicyAttachPdfRequest(BaseModel):
    """Request payload for attaching a generated PDF URL to an issued policy.

    Attributes:
        pdf_url: Generated PDF URL for the issued policy.
    """

    pdf_url: str = Field(..., description="Generated PDF URL for the issued policy")

    model_config = ConfigDict(extra="forbid")

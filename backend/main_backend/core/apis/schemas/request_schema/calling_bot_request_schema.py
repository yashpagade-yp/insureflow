"""Request schemas for calling-bot APIs in the main backend."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CallingBotStartCallRequest(BaseModel):
    """Request payload for starting one outbound bot call.

    Attributes:
        customer_name: Target customer name.
        customer_phone: Destination customer phone number.
        customer_email: Optional customer email for later policy delivery.
        desired_coverage_amount: Optional initial coverage amount known before
            the call starts.
        notes: Optional operator notes about the purpose of the call.
    """

    customer_name: str = Field(..., description="Target customer name")
    customer_phone: str = Field(..., description="Destination customer phone number")
    customer_email: str | None = Field(default=None, description="Optional customer email")
    desired_coverage_amount: float | None = Field(
        default=None,
        ge=0,
        description="Optional initial coverage amount known before the call",
    )
    notes: str | None = Field(default=None, description="Optional operator notes")

    model_config = ConfigDict(extra="forbid")


class CallingBotCompletePurchaseRequest(BaseModel):
    """Request payload for completing a calling-bot purchase flow.

    Attributes:
        selected_plan_id: Provider plan identifier chosen by the customer.
        payment_otp: Mock payment OTP provided by the customer during the call.
    """

    selected_plan_id: str = Field(..., description="Provider plan identifier chosen by the customer")
    payment_otp: str = Field(
        ...,
        min_length=4,
        max_length=8,
        description="Mock payment OTP provided by the customer during the call",
    )

    model_config = ConfigDict(extra="forbid")


class CallingBotPreparePurchaseRequest(BaseModel):
    """Request payload for preparing a mock payment OTP for one bot call.

    Attributes:
        selected_plan_id: Provider plan identifier chosen by the customer.
    """

    selected_plan_id: str = Field(
        ...,
        description="Provider plan identifier chosen by the customer",
    )

    model_config = ConfigDict(extra="forbid")

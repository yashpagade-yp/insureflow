"""Request schemas for payment-related APIs in the provider backend."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreateRequest(BaseModel):
    """Request payload for creating a provider-side payment record.

    Attributes:
        transaction_id: Transaction identifier for the payment journey.
        user_id: User identifier linked to the payment.
        amount: Final payable amount recorded for the payment.
    """

    transaction_id: str = Field(..., description="Transaction identifier for the payment journey")
    user_id: str = Field(..., description="User identifier linked to the payment")
    amount: float = Field(..., ge=0, description="Final payable amount recorded for the payment")

    model_config = ConfigDict(extra="forbid")


class PaymentOtpVerifyRequest(BaseModel):
    """Request payload for verifying a mock payment OTP.

    Attributes:
        transaction_id: Transaction identifier for the payment journey.
        payment_reference: Payment reference to verify.
        otp: Plain OTP value entered by the customer.
    """

    transaction_id: str = Field(..., description="Transaction identifier for the payment journey")
    payment_reference: str = Field(..., description="Payment reference to verify")
    otp: str = Field(
        ...,
        min_length=4,
        max_length=8,
        description="Plain OTP value entered by the customer",
    )

    model_config = ConfigDict(extra="forbid")

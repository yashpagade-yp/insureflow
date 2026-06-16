"""Response schemas for payment-related APIs in the provider backend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreateResponse(BaseModel):
    """Response payload returned after creating a payment record.

    Attributes:
        message: Human-readable response message.
        transaction_id: Transaction identifier for the payment journey.
        payment_reference: Generated payment reference.
        payment_status: Current payment status.
        amount: Final payable amount.
        gateway_url: Mock gateway URL for the payment page.
        created_at: Timestamp when the payment record was created.
    """

    message: str = Field(..., description="Human-readable response message")
    transaction_id: str = Field(..., description="Transaction identifier for the journey")
    payment_reference: str = Field(..., description="Generated payment reference")
    payment_status: str = Field(..., description="Current payment status")
    amount: float = Field(..., ge=0, description="Final payable amount")
    gateway_url: str | None = Field(default=None, description="Mock payment gateway URL")
    created_at: datetime = Field(..., description="Payment record creation timestamp")

    model_config = ConfigDict(extra="forbid")


class PaymentOtpSendResponse(BaseModel):
    """Response payload returned after sending a payment OTP.

    Attributes:
        message: Human-readable response message.
        payment_reference: Payment reference for the current payment.
        otp_expires_at: Timestamp when the payment OTP expires.
        plain_otp: Mock OTP value exposed only for local development flows.
    """

    message: str = Field(..., description="Human-readable response message")
    payment_reference: str = Field(..., description="Payment reference for the current payment")
    otp_expires_at: datetime = Field(..., description="Timestamp when the payment OTP expires")
    plain_otp: str | None = Field(
        default=None,
        description="Mock OTP value exposed only for local development flows",
    )

    model_config = ConfigDict(extra="forbid")


class PaymentOtpVerifyResponse(BaseModel):
    """Response payload returned after verifying a payment OTP.

    Attributes:
        message: Human-readable response message.
        transaction_id: Transaction identifier for the journey.
        payment_reference: Payment reference for the current payment.
        payment_status: Updated payment status.
        verified_at: Timestamp when the OTP was verified.
    """

    message: str = Field(..., description="Human-readable response message")
    transaction_id: str = Field(..., description="Transaction identifier for the journey")
    payment_reference: str = Field(..., description="Payment reference for the current payment")
    payment_status: str = Field(..., description="Updated payment status")
    verified_at: datetime = Field(..., description="Timestamp when the OTP was verified")

    model_config = ConfigDict(extra="forbid")


class PaymentStatusResponse(BaseModel):
    """Represents payment status details returned to the client.

    Attributes:
        transaction_id: Transaction identifier for the payment journey.
        payment_reference: Payment reference for the current payment.
        payment_status: Current payment status.
        amount: Recorded payment amount.
        gateway_url: Mock payment gateway URL.
        updated_at: Payment last-update timestamp.
    """

    transaction_id: str = Field(..., description="Transaction identifier for the journey")
    payment_reference: str = Field(..., description="Payment reference for the current payment")
    payment_status: str = Field(..., description="Current payment status")
    amount: float = Field(..., ge=0, description="Recorded payment amount")
    gateway_url: str | None = Field(default=None, description="Mock payment gateway URL")
    updated_at: datetime = Field(..., description="Payment last-update timestamp")

    model_config = ConfigDict(extra="forbid")


class PaymentListResponse(BaseModel):
    """Represents a list of payment records returned to the provider admin.

    Attributes:
        items: Returned payment records.
        total_count: Total number of returned payment records.
    """

    items: list[PaymentStatusResponse] = Field(
        default_factory=list,
        description="Returned payment records",
    )
    total_count: int = Field(..., ge=0, description="Total number of returned payments")

    model_config = ConfigDict(extra="forbid")

"""Payment models for the InsureFlow provider backend.

This module contains the provider-side payment document model used for
transaction-linked payment records. The structure follows the current project
specification and the ODMantic-based project pattern.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from odmantic import Field, Model
from odmantic.config import ODMConfigDict
from pydantic import BaseModel


def generate_payment_reference() -> str:
    """Generate a unique business-facing payment reference."""

    return f"PAY-{uuid4().hex[:12].upper()}"


class PaymentStatus(str, Enum):
    """Defines the supported lifecycle states for a payment record.

    Attributes:
        PENDING: Payment is created but not yet completed.
        SUCCESS: Payment completed successfully.
        FAILED: Payment attempt failed.
    """

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class PaymentOtp(BaseModel):
    """Represents the mock payment OTP state embedded inside a payment.

    Attributes:
        code_hash: Hashed OTP value used for payment confirmation.
        expires_at: Timestamp when the payment OTP becomes invalid.
        requested_at: Timestamp when the payment OTP was generated.
        attempt_count: Number of failed verification attempts.
        attempt_window_started_at: Timestamp when the current payment OTP
            attempt window started.
        verified_at: Timestamp when the payment OTP was successfully verified.
    """

    code_hash: str = Field(..., description="Hashed OTP value for payment verification")
    expires_at: datetime = Field(
        ...,
        description="Timestamp when the payment OTP expires",
    )
    requested_at: datetime = Field(
        ...,
        description="Timestamp when the payment OTP was requested",
    )
    attempt_count: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Number of failed payment OTP verification attempts",
    )
    attempt_window_started_at: datetime = Field(
        ...,
        description="Timestamp when the current payment OTP attempt window started",
    )
    verified_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the payment OTP was verified",
    )


class Payment(Model):
    """Represents a payment document stored in the `payments` collection.

    Each payment is linked to a transaction and user. The current scope keeps
    the payment flow simple and mock-friendly while preserving business-facing
    payment references and status tracking.

    Attributes:
        transaction_id: Identifier of the related transaction.
        user_id: Identifier of the user who made the payment.
        amount: Payment amount recorded for the transaction.
        payment_method: Payment method used for the transaction.
        payment_reference: Unique business-facing payment reference.
        payment_status: Current payment status.
        gateway_url: Mock payment gateway URL shown to the customer.
        payment_otp: Embedded OTP state for mock payment confirmation.
        created_at: UTC timestamp when the payment record was created.
        updated_at: UTC timestamp when the payment record was last updated.
    """

    transaction_id: str = Field(
        ...,
        description="Identifier of the related transaction",
    )
    user_id: str = Field(..., description="Identifier of the user who made the payment")
    amount: float = Field(..., ge=0, description="Amount recorded for the payment")
    payment_method: str = Field(
        default="mock_gateway",
        description="Payment method used for the transaction",
    )
    payment_reference: str = Field(
        default_factory=generate_payment_reference,
        unique=True,
        description="Unique business-facing payment reference",
    )
    payment_status: PaymentStatus = Field(
        default=PaymentStatus.PENDING,
        description="Current status of the payment",
    )
    gateway_url: Optional[str] = Field(
        default=None,
        description="Mock payment gateway URL used to open the payment page",
    )
    payment_otp: Optional[PaymentOtp] = Field(
        default=None,
        description="Embedded OTP state used for mock payment confirmation",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the payment record was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the payment record was last updated",
    )

    model_config = ODMConfigDict(
        collection="payments",
        extra="forbid",
    )


PaymentModel = Payment

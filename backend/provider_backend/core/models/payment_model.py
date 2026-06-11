"""Payment models for the InsureFlow provider backend.

This module contains the provider-side payment document model used for
transaction-linked payment records. The structure follows the current project
specification and the ODMantic-based project pattern.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from odmantic import Field, Model
from odmantic.config import ODMConfigDict


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
        created_at: UTC timestamp when the payment record was created.
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
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the payment record was created",
    )

    model_config = ODMConfigDict(
        collection="payments",
        extra="forbid",
    )


PaymentModel = Payment

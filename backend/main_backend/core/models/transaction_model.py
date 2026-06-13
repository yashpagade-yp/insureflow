"""Transaction models for the InsureFlow main backend.

This module contains the transaction document model and its embedded status
history structure. The model follows the ODMantic-based project pattern while
keeping the transaction lifecycle defined in `models.txt`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from odmantic import Field, Model
from odmantic.config import ODMConfigDict
from pydantic import BaseModel


def generate_transaction_id() -> str:
    """Generate a unique UUID-based transaction identifier."""

    return str(uuid4())


class TransactionStatus(str, Enum):
    """Defines the supported states in the transaction lifecycle.

    Attributes:
        FORM_SUBMITTED: Insurance details have been submitted.
        OFFERS_RECEIVED: Matching offers have been generated.
        OFFER_SELECTED: One offer has been selected by the user.
        ADD_ONS_SELECTED: Plan add-ons have been selected.
        OFFER_CONFIRMED: Final offer confirmation is complete.
        PAYMENT_PENDING: Payment is awaiting completion.
        PURCHASED: Purchase flow completed successfully.
        PAYMENT_FAILED: Payment attempt failed.
    """

    FORM_SUBMITTED = "FORM_SUBMITTED"
    OFFERS_RECEIVED = "OFFERS_RECEIVED"
    OFFER_SELECTED = "OFFER_SELECTED"
    ADD_ONS_SELECTED = "ADD_ONS_SELECTED"
    OFFER_CONFIRMED = "OFFER_CONFIRMED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PURCHASED = "PURCHASED"
    PAYMENT_FAILED = "PAYMENT_FAILED"


class StatusHistoryEntry(BaseModel):
    """Represents one recorded transaction status transition.

    Attributes:
        status: Status reached at the recorded point in time.
        timestamp: UTC timestamp when the status was recorded.
    """

    status: TransactionStatus = Field(..., description="Recorded transaction status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp for the status transition",
    )


class TransactionV1(Model):
    """Represents a transaction document stored in the `transactions` collection.

    Each transaction belongs to one user and tracks the full insurance journey
    through explicit status transitions. The `transaction_id` is a UUID string
    used for cross-service linking.

    Attributes:
        transaction_id: Unique UUID-based business identifier for the
            transaction.
        user_id: Identifier of the user who owns the transaction.
        current_status: Current lifecycle status of the transaction.
        status_history: Ordered history of status transition events.
        last_active_at: UTC timestamp of the latest user or system activity on
            the transaction.
        selected_plan_id: Optional selected provider plan identifier for the
            journey.
        completed_at: UTC timestamp when the transaction finished
            successfully.
        created_at: UTC timestamp when the transaction was created.
        updated_at: UTC timestamp for the latest transaction update.
    """

    transaction_id: str = Field(
        default_factory=generate_transaction_id,
        unique=True,
        description="UUID-based transaction identifier used across services",
    )
    user_id: str = Field(..., description="Identifier of the user who owns the transaction")
    current_status: TransactionStatus = Field(
        default=TransactionStatus.FORM_SUBMITTED,
        description="Current lifecycle status of the transaction",
    )
    status_history: list[StatusHistoryEntry] = Field(
        default_factory=lambda: [
            StatusHistoryEntry(status=TransactionStatus.FORM_SUBMITTED)
        ],
        description="Chronological history of transaction status transitions",
    )
    last_active_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the latest activity on the transaction",
    )
    selected_plan_id: str | None = Field(
        default=None,
        description="Optional selected provider plan identifier",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when the transaction completed successfully",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the transaction was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the transaction was last updated",
    )

    model_config = ODMConfigDict(
        collection="transactions",
        extra="forbid",
    )


TransactionModel = TransactionV1

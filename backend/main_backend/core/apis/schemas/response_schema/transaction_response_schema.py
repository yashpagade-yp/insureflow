"""Response schemas for transaction-related APIs in the main backend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ....models.transaction_model import TransactionStatus


class TransactionResponse(BaseModel):
    """Represents one transaction returned by the main backend.

    Attributes:
        transaction_id: Business transaction identifier.
        user_id: User identifier linked to the transaction.
        current_status: Current transaction status.
        selected_plan_id: Optional selected provider plan identifier.
        last_active_at: Latest activity timestamp.
        completed_at: Optional completion timestamp for a finished transaction.
        created_at: Transaction creation timestamp.
        updated_at: Transaction last-update timestamp.
    """

    transaction_id: str = Field(..., description="Business transaction identifier")
    user_id: str = Field(..., description="User identifier linked to the transaction")
    current_status: TransactionStatus = Field(..., description="Current transaction status")
    selected_plan_id: str | None = Field(
        default=None,
        description="Selected provider plan identifier for the transaction",
    )
    last_active_at: datetime = Field(..., description="Latest activity timestamp")
    completed_at: datetime | None = Field(
        default=None,
        description="Completion timestamp for a finished transaction",
    )
    created_at: datetime = Field(..., description="Transaction creation timestamp")
    updated_at: datetime = Field(..., description="Transaction last-update timestamp")


class TransactionListResponse(BaseModel):
    """Represents a list of transactions returned for a user.

    Attributes:
        items: List of returned transaction records.
        total_count: Total number of returned transactions.
    """

    items: list[TransactionResponse] = Field(
        default_factory=list,
        description="List of transactions",
    )
    total_count: int = Field(..., ge=0, description="Total number of returned transactions")

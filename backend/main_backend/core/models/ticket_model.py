"""Ticket models for the InsureFlow main backend.

This module contains the support ticket document model used to track customer
issues related to transactions and policies. The structure follows the current
project specification and the ODMantic-based project pattern.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from odmantic import Field, Model
from odmantic.config import ODMConfigDict


def generate_ticket_id() -> str:
    """Generate a unique business-facing ticket identifier."""

    return f"TKT-{uuid4().hex[:12].upper()}"


class TicketStatus(str, Enum):
    """Defines the supported lifecycle states for a support ticket.

    Attributes:
        OPEN: Ticket has been created and is awaiting handling.
        IN_PROGRESS: Ticket is currently being worked on.
        RESOLVED: Ticket has been resolved by the assigned admin.
        CLOSED: Ticket has been formally closed.
    """

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Ticket(Model):
    """Represents a support ticket stored in the `tickets` collection.

    Each ticket belongs to a user and is typically linked to a transaction.
    Admin users can respond to the ticket, update its status, and mark it as
    resolved when appropriate.

    Attributes:
        ticket_id: Unique business-facing ticket reference.
        user_id: Identifier of the user who created the ticket.
        transaction_id: Identifier of the related transaction.
        issue_type: Short category describing the type of issue.
        description: Detailed description of the user's issue.
        ticket_status: Current lifecycle status of the ticket.
        admin_id: Optional identifier of the admin handling the ticket.
        admin_response: Optional latest response from the assigned admin.
        resolved_at: Optional UTC timestamp when the ticket was resolved.
        created_at: UTC timestamp when the ticket was created.
        updated_at: UTC timestamp when the ticket was last updated.
    """

    ticket_id: str = Field(
        default_factory=generate_ticket_id,
        unique=True,
        description="Unique business-facing ticket identifier",
    )
    user_id: str = Field(..., description="Identifier of the user who created the ticket")
    transaction_id: str = Field(
        ...,
        description="Identifier of the transaction linked to this ticket",
    )
    issue_type: str = Field(..., description="Category of issue reported by the user")
    description: str = Field(..., description="Detailed explanation of the support issue")
    ticket_status: TicketStatus = Field(
        default=TicketStatus.OPEN,
        description="Current lifecycle status of the ticket",
    )
    admin_id: Optional[str] = Field(
        default=None,
        description="Optional identifier of the admin assigned to the ticket",
    )
    admin_response: Optional[str] = Field(
        default=None,
        description="Optional response provided by the assigned admin",
    )
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the ticket was resolved",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the ticket was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the ticket was last updated",
    )

    model_config = ODMConfigDict(
        collection="tickets",
        extra="forbid",
    )


TicketModel = Ticket

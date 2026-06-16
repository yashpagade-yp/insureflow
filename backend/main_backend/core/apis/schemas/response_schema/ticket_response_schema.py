"""Response schemas for support ticket APIs in the main backend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TicketResponse(BaseModel):
    """Represents one support ticket returned by the main backend.

    Attributes:
        ticket_id: Business-facing ticket identifier.
        user_id: Identifier of the user who created the ticket.
        transaction_id: Related transaction identifier.
        issue_type: Issue category selected by the user.
        description: Detailed issue description submitted by the user.
        ticket_status: Current ticket status.
        admin_id: Optional admin identifier assigned to the ticket.
        admin_response: Optional latest admin response message.
        resolved_at: Optional timestamp when the ticket was resolved.
        created_at: Ticket creation timestamp.
        updated_at: Ticket last-update timestamp.
    """

    ticket_id: str = Field(..., description="Business-facing ticket identifier")
    user_id: str = Field(..., description="Identifier of the user who created the ticket")
    transaction_id: str = Field(..., description="Related transaction identifier")
    issue_type: str = Field(..., description="Issue category")
    description: str = Field(..., description="Detailed issue description")
    ticket_status: str = Field(..., description="Current ticket status")
    admin_id: str | None = Field(default=None, description="Assigned admin identifier")
    admin_response: str | None = Field(default=None, description="Latest admin response")
    resolved_at: datetime | None = Field(default=None, description="Resolution timestamp")
    created_at: datetime = Field(..., description="Ticket creation timestamp")
    updated_at: datetime = Field(..., description="Ticket last-update timestamp")

    model_config = ConfigDict(extra="forbid")


class TicketListResponse(BaseModel):
    """Represents a list of support tickets for a user or admin view.

    Attributes:
        items: List of returned ticket records.
        total_count: Total number of returned tickets.
    """

    items: list[TicketResponse] = Field(default_factory=list, description="List of tickets")
    total_count: int = Field(..., ge=0, description="Total number of tickets returned")

    model_config = ConfigDict(extra="forbid")

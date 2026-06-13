"""Request schemas for support ticket APIs in the main backend."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TicketCreateRequest(BaseModel):
    """Request payload for creating a new support ticket.

    Attributes:
        transaction_id: Related transaction identifier.
        issue_type: Short category describing the issue.
        description: Detailed explanation of the issue.
    """

    transaction_id: str = Field(..., description="Related transaction identifier")
    issue_type: str = Field(..., description="Short category describing the issue")
    description: str = Field(..., min_length=5, description="Detailed issue description")

    model_config = ConfigDict(extra="forbid")


class TicketUpdateRequest(BaseModel):
    """Request payload for updating a user's support ticket.

    Attributes:
        issue_type: Updated issue category.
        description: Updated issue description.
    """

    issue_type: str | None = Field(default=None, description="Updated issue category")
    description: str | None = Field(default=None, description="Updated issue description")

    model_config = ConfigDict(extra="forbid")


class TicketAdminResponseRequest(BaseModel):
    """Request payload for admin action on a support ticket.

    Attributes:
        ticket_status: Updated ticket status.
        admin_response: Admin response message for the ticket.
    """

    ticket_status: str = Field(..., description="Updated ticket status")
    admin_response: str = Field(..., description="Admin response message")

    model_config = ConfigDict(extra="forbid")

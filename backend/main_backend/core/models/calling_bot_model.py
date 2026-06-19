"""Calling-bot models for customer-journey voice interactions.

This module stores outbound calling-bot sessions triggered from the
customer-app admin side. The records keep safe metadata about the call,
captured voice-flow decisions, recommended plans, and the final purchase
result when the call converts into a completed insurance journey.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from odmantic import Field, Model
from odmantic.config import ODMConfigDict
from pydantic import BaseModel
from pydantic import Field as PydanticField


def generate_call_reference() -> str:
    """Generate a stable UUID-based reference for one bot call."""

    return str(uuid4())


class CallDirection(str, Enum):
    """Defines the supported call directions."""

    OUTBOUND = "outbound"
    INBOUND = "inbound"


class CallStatus(str, Enum):
    """Defines the supported calling-bot call states."""

    QUEUED = "queued"
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no-answer"
    BUSY = "busy"
    CANCELED = "canceled"


class CustomerInterestStatus(str, Enum):
    """Defines whether the customer wants to continue the insurance flow."""

    UNKNOWN = "unknown"
    INTERESTED = "interested"
    NOT_INTERESTED = "not-interested"


class PolicyEmailStatus(str, Enum):
    """Defines policy-email delivery state stored on a bot call record."""

    NOT_TRIGGERED = "not-triggered"
    SENT = "sent"
    FAILED = "failed"


class RecommendedPlanSnapshot(BaseModel):
    """Represents one plan recommendation stored on a bot call record.

    Attributes:
        plan_id: Provider plan identifier.
        company_name: Provider company name.
        plan_name: Recommended plan name.
        coverage_amount: Coverage amount on the plan.
        total_premium: Total premium shown to the caller.
    """

    plan_id: str = PydanticField(..., description="Provider plan identifier")
    company_name: str = PydanticField(..., description="Provider company name")
    plan_name: str = PydanticField(..., description="Recommended plan name")
    coverage_amount: float = PydanticField(..., ge=0, description="Coverage amount on the plan")
    total_premium: float = PydanticField(..., ge=0, description="Total premium on the plan")


class CallingBotCall(Model):
    """Represents one Twilio-backed customer calling-bot session.

    Attributes:
        call_reference: Internal UUID reference used before and after Twilio
            creates the real call SID.
        call_sid: Optional Twilio call SID once the call is accepted by Twilio.
        customer_name: Name used for the call target.
        customer_phone: Destination mobile number dialled by the bot.
        customer_email: Optional customer email linked to the journey.
        direction: Call direction, currently outbound.
        calling_type: Human-readable channel label for the UI.
        status: Latest call status from Twilio or internal flow.
        customer_interest: Whether the customer wants to continue the flow.
        desired_coverage_amount: Coverage amount captured during the call.
        transcript_lines: Lightweight transcript/log lines captured by the bot.
        recommended_plans: Plans matched after the call captures coverage amount.
        transaction_id: Optional created transaction after turning the call into
            a real customer journey.
        user_id: Optional linked user identifier.
        selected_plan_id: Optional selected provider plan id.
        selected_plan_name: Optional selected provider plan name.
        provider_company_name: Optional provider company chosen for purchase.
        payment_reference: Optional payment reference created during purchase.
        payment_status: Optional payment status string.
        policy_number: Optional issued policy number.
        policy_pdf_url: Optional generated policy PDF URL.
        policy_email_status: Whether the policy email was sent successfully.
        duration_seconds: Optional completed call duration in seconds.
        started_by_admin_id: Admin user identifier who triggered the call.
        started_by_admin_email: Admin email used for the trigger action.
        from_number: Twilio outbound caller id.
        summary: Human-readable call summary for the frontend.
        last_error: Optional last error message.
        created_at: UTC timestamp when the record was created.
        updated_at: UTC timestamp when the record was last updated.
        completed_at: UTC timestamp when the call or purchase flow completed.
    """

    call_reference: str = Field(
        default_factory=generate_call_reference,
        unique=True,
        description="Stable UUID reference for one calling-bot session",
    )
    call_sid: str | None = Field(
        default=None,
        unique=True,
        description="Twilio call SID once the outbound call is created",
    )
    customer_name: str = Field(..., description="Name used for the call target")
    customer_phone: str = Field(..., description="Destination mobile number dialled by the bot")
    customer_email: str | None = Field(
        default=None,
        description="Optional customer email linked to the journey",
    )
    direction: CallDirection = Field(
        default=CallDirection.OUTBOUND,
        description="Direction of the calling-bot session",
    )
    calling_type: str = Field(
        default="voice",
        description="Human-readable channel label for the frontend",
    )
    status: CallStatus = Field(
        default=CallStatus.QUEUED,
        description="Latest outbound call status",
    )
    customer_interest: CustomerInterestStatus = Field(
        default=CustomerInterestStatus.UNKNOWN,
        description="Whether the customer wants to continue the purchase journey",
    )
    desired_coverage_amount: float | None = Field(
        default=None,
        ge=0,
        description="Coverage amount captured during the call",
    )
    transcript_lines: list[str] = Field(
        default_factory=list,
        description="Lightweight transcript or event log for the call",
    )
    recommended_plans: list[RecommendedPlanSnapshot] = Field(
        default_factory=list,
        description="Plans recommended during the voice-flow",
    )
    transaction_id: str | None = Field(
        default=None,
        description="Linked customer journey transaction identifier",
    )
    user_id: str | None = Field(
        default=None,
        description="Linked user identifier created during the journey",
    )
    selected_plan_id: str | None = Field(
        default=None,
        description="Selected provider plan identifier",
    )
    selected_plan_name: str | None = Field(
        default=None,
        description="Selected provider plan name",
    )
    provider_company_name: str | None = Field(
        default=None,
        description="Provider company chosen for the final policy",
    )
    payment_reference: str | None = Field(
        default=None,
        description="Payment reference created during purchase",
    )
    payment_status: str | None = Field(
        default=None,
        description="Latest payment status recorded on the call",
    )
    policy_number: str | None = Field(
        default=None,
        description="Issued policy number after a successful purchase",
    )
    policy_pdf_url: str | None = Field(
        default=None,
        description="Generated policy PDF URL after purchase completion",
    )
    policy_email_status: PolicyEmailStatus = Field(
        default=PolicyEmailStatus.NOT_TRIGGERED,
        description="Policy-email delivery state for the call flow",
    )
    duration_seconds: int | None = Field(
        default=None,
        ge=0,
        description="Completed call duration in seconds",
    )
    started_by_admin_id: str = Field(
        ...,
        description="Admin user identifier who triggered the outbound call",
    )
    started_by_admin_email: str = Field(
        ...,
        description="Admin email used to trigger the outbound call",
    )
    from_number: str | None = Field(
        default=None,
        description="Twilio outbound caller id used for the call",
    )
    summary: str | None = Field(
        default=None,
        description="Human-readable call summary for the frontend",
    )
    last_error: str | None = Field(
        default=None,
        description="Optional last error message stored on the call",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the call record was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the call record was last updated",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when the call or purchase flow completed",
    )

    model_config = ODMConfigDict(
        collection="calling_bot_calls",
        extra="forbid",
    )


CallingBotCallModel = CallingBotCall

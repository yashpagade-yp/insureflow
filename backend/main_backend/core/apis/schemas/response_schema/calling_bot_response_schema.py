"""Response schemas for calling-bot APIs in the main backend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CallingBotPlanResponse(BaseModel):
    """Represents one recommended plan stored on a calling-bot call record."""

    plan_id: str = Field(..., description="Provider plan identifier")
    company_name: str = Field(..., description="Provider company name")
    plan_name: str = Field(..., description="Recommended plan name")
    coverage_amount: float = Field(..., ge=0, description="Coverage amount on the plan")
    total_premium: float = Field(..., ge=0, description="Total premium on the plan")

    model_config = ConfigDict(extra="forbid")


class CallingBotConfigResponse(BaseModel):
    """Safe frontend configuration returned for the calling-bot section."""

    bot_name: str = Field(..., description="Display name of the calling bot")
    channel: str = Field(..., description="Human-readable channel label")
    mode: str = Field(..., description="Current call mode, such as outbound-only")
    trigger_owner: str = Field(..., description="Who is allowed to trigger the call")
    backend_name: str = Field(..., description="Backend that owns the bot flow")
    twilio_from_number: str | None = Field(default=None, description="Configured Twilio outbound number")
    twilio_test_to_number: str | None = Field(default=None, description="Configured default test target number")
    masked_account_sid: str | None = Field(default=None, description="Masked Twilio account SID")
    auth_token_configured: bool = Field(..., description="Whether the Twilio auth token is configured")
    webhook_base_url: str | None = Field(default=None, description="Configured public base URL used for Twilio callbacks")
    conversation_steps: list[str] = Field(default_factory=list, description="High-level bot conversation steps")

    model_config = ConfigDict(extra="forbid")


class CallingBotCallResponse(BaseModel):
    """Represents a summarized calling-bot call for list views."""

    call_reference: str = Field(..., description="Stable internal call reference")
    call_sid: str | None = Field(default=None, description="Twilio call SID")
    customer_name: str = Field(..., description="Target customer name")
    customer_phone: str = Field(..., description="Target customer phone number")
    direction: str = Field(..., description="Call direction")
    calling_type: str = Field(..., description="Human-readable channel label")
    status: str = Field(..., description="Latest call status")
    customer_interest: str = Field(..., description="Customer interest decision")
    desired_coverage_amount: float | None = Field(default=None, description="Captured coverage amount")
    duration_seconds: int | None = Field(default=None, description="Completed call duration in seconds")
    recommended_plan_count: int = Field(..., ge=0, description="Number of recommended plans on the call")
    selected_plan_name: str | None = Field(default=None, description="Selected plan name")
    policy_number: str | None = Field(default=None, description="Issued policy number")
    policy_email_status: str = Field(..., description="Policy-email delivery state")
    created_at: datetime = Field(..., description="Call record creation timestamp")
    updated_at: datetime = Field(..., description="Call record update timestamp")

    model_config = ConfigDict(extra="forbid")


class CallingBotCallListResponse(BaseModel):
    """Represents a list of calling-bot calls."""

    items: list[CallingBotCallResponse] = Field(default_factory=list, description="Ordered call summaries")
    total_count: int = Field(..., ge=0, description="Total number of call summaries")

    model_config = ConfigDict(extra="forbid")


class CallingBotCallDetailResponse(BaseModel):
    """Represents one detailed calling-bot call record."""

    call_reference: str = Field(..., description="Stable internal call reference")
    call_sid: str | None = Field(default=None, description="Twilio call SID")
    customer_name: str = Field(..., description="Target customer name")
    customer_phone: str = Field(..., description="Target customer phone number")
    customer_email: str | None = Field(default=None, description="Linked customer email")
    direction: str = Field(..., description="Call direction")
    calling_type: str = Field(..., description="Human-readable channel label")
    status: str = Field(..., description="Latest call status")
    customer_interest: str = Field(..., description="Customer interest decision")
    desired_coverage_amount: float | None = Field(default=None, description="Captured coverage amount")
    transaction_id: str | None = Field(default=None, description="Linked transaction identifier")
    user_id: str | None = Field(default=None, description="Linked user identifier")
    selected_plan_id: str | None = Field(default=None, description="Selected plan identifier")
    selected_plan_name: str | None = Field(default=None, description="Selected plan name")
    provider_company_name: str | None = Field(default=None, description="Selected provider company")
    payment_reference: str | None = Field(default=None, description="Linked payment reference")
    payment_status: str | None = Field(default=None, description="Latest payment status")
    policy_number: str | None = Field(default=None, description="Issued policy number")
    policy_pdf_url: str | None = Field(default=None, description="Generated policy PDF URL")
    policy_email_status: str = Field(..., description="Policy-email delivery state")
    duration_seconds: int | None = Field(default=None, description="Completed call duration in seconds")
    from_number: str | None = Field(default=None, description="Configured Twilio caller id used for the call")
    summary: str | None = Field(default=None, description="Human-readable call summary")
    transcript_lines: list[str] = Field(default_factory=list, description="Transcript or event log lines")
    recommended_plans: list[CallingBotPlanResponse] = Field(default_factory=list, description="Recommended plans captured on the call")
    last_error: str | None = Field(default=None, description="Last stored error message")
    started_by_admin_id: str = Field(..., description="Admin identifier who started the call")
    started_by_admin_email: str = Field(..., description="Admin email who started the call")
    created_at: datetime = Field(..., description="Call record creation timestamp")
    updated_at: datetime = Field(..., description="Call record update timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")

    model_config = ConfigDict(extra="forbid")


class CallingBotStartCallResponse(BaseModel):
    """Represents the response returned after starting one outbound call."""

    message: str = Field(..., description="Human-readable response message")
    call_reference: str = Field(..., description="Stable internal call reference")
    call_sid: str | None = Field(default=None, description="Twilio call SID")
    status: str = Field(..., description="Latest call status after creation")
    from_number: str | None = Field(default=None, description="Configured Twilio caller id")
    to_number: str = Field(..., description="Destination customer phone number")
    created_at: datetime = Field(..., description="Call record creation timestamp")

    model_config = ConfigDict(extra="forbid")


class CallingBotCompletePurchaseResponse(BaseModel):
    """Represents the final purchase result for a calling-bot session."""

    message: str = Field(..., description="Human-readable response message")
    call_reference: str = Field(..., description="Stable internal call reference")
    transaction_id: str = Field(..., description="Linked transaction identifier")
    selected_plan_id: str = Field(..., description="Selected provider plan identifier")
    payment_reference: str = Field(..., description="Payment reference created for the purchase")
    payment_status: str = Field(..., description="Final payment status")
    policy_number: str | None = Field(default=None, description="Issued policy number")
    policy_pdf_url: str | None = Field(default=None, description="Generated policy PDF URL")
    policy_email_status: str = Field(..., description="Policy-email delivery state")

    model_config = ConfigDict(extra="forbid")


class CallingBotPreparePurchaseResponse(BaseModel):
    """Represents the mock OTP preparation result for a bot purchase."""

    message: str = Field(..., description="Human-readable response message")
    call_reference: str = Field(..., description="Stable internal call reference")
    transaction_id: str = Field(..., description="Linked transaction identifier")
    selected_plan_id: str = Field(..., description="Selected provider plan identifier")
    selected_plan_name: str = Field(..., description="Selected provider plan name")
    provider_company_name: str = Field(..., description="Selected provider company")
    payment_reference: str = Field(..., description="Payment reference created for the purchase")
    payment_status: str = Field(..., description="Current payment status after OTP generation")
    otp_expires_at: datetime = Field(..., description="Mock OTP expiry timestamp")
    plain_otp: str | None = Field(
        default=None,
        description="Mock OTP preview returned for local development flow",
    )

    model_config = ConfigDict(extra="forbid")

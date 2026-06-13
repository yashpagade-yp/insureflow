"""Response schemas for insurance-detail APIs in the main backend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ....models.insurance_detail_model import InsuranceType
from ....models.transaction_model import TransactionStatus


class InsuranceDetailCreateResponse(BaseModel):
    """Response payload returned after creating a new insurance-detail journey.

    Attributes:
        user_id: Customer identifier linked to the new journey.
        transaction_id: Transaction identifier created for the journey.
        insurance_detail_id: Insurance-detail identifier created for the journey.
        current_status: Current transaction status.
        form_step: Latest saved form step.
    """

    user_id: str = Field(..., description="Customer identifier linked to the journey")
    transaction_id: str = Field(..., description="Transaction identifier for the journey")
    insurance_detail_id: str = Field(
        ...,
        description="Insurance-detail identifier created for the journey",
    )
    current_status: TransactionStatus = Field(..., description="Current transaction status")
    form_step: str | None = Field(default=None, description="Latest saved form step")


class InsuranceDetailUpdateResponse(BaseModel):
    """Response payload returned after updating an insurance detail.

    Attributes:
        message: Human-readable response message.
        transaction_id: Transaction identifier for the updated journey.
        insurance_detail_id: Insurance-detail identifier.
        current_status: Current transaction status after update.
        form_step: Latest saved form step after update.
    """

    message: str = Field(..., description="Human-readable response message")
    transaction_id: str = Field(..., description="Transaction identifier for the journey")
    insurance_detail_id: str = Field(..., description="Insurance-detail identifier")
    current_status: TransactionStatus = Field(..., description="Current transaction status")
    form_step: str | None = Field(default=None, description="Latest saved form step")


class LatestIncompleteInsuranceDetailResponse(BaseModel):
    """Response payload for resuming the latest incomplete insurance journey.

    Attributes:
        user_id: Customer identifier linked to the incomplete journey.
        transaction_id: Latest incomplete transaction identifier.
        current_status: Current transaction status of the incomplete journey.
        form_step: Latest saved form step for the incomplete journey.
        insurance_type: Insurance category of the incomplete journey.
        last_active_at: Timestamp of the latest activity on the transaction.
        insurance_detail_id: Insurance-detail identifier for the incomplete journey.
    """

    user_id: str = Field(..., description="Customer identifier linked to the journey")
    transaction_id: str = Field(..., description="Latest incomplete transaction identifier")
    current_status: TransactionStatus = Field(..., description="Current transaction status")
    form_step: str | None = Field(default=None, description="Latest saved form step")
    insurance_type: InsuranceType = Field(..., description="Insurance category of the journey")
    last_active_at: datetime = Field(..., description="Latest activity timestamp")
    insurance_detail_id: str = Field(..., description="Insurance-detail identifier")

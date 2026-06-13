"""API routes for the InsureFlow main backend."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from odmantic import ObjectId
from pydantic import BaseModel, Field

from ..database.database import get_engine
from ..models.insurance_detail_model import (
    InsuranceDetailModel,
    InsuranceType,
)
from ..models.transaction_model import TransactionModel, TransactionStatus
from ..models.user_model import UserModel


router = APIRouter(prefix="/v1", tags=["main-backend"])


class JourneyStartRequest(BaseModel):
    """Request body for creating a new user journey."""

    mobile_number: str = Field(..., min_length=10, description="Customer mobile number")
    insurance_type: InsuranceType
    proposer_first_name: str | None = None
    proposer_last_name: str | None = None
    proposer_email: str | None = None
    proposer_dob: date | None = None
    proposer_gender: str | None = None
    insured_members: list[dict[str, Any]] = Field(default_factory=list)
    sum_insured_requested: float | None = Field(default=None, ge=0)
    policy_term_years: int | None = Field(default=None, ge=1)
    premium_preference: str | None = None
    occupation: str | None = None
    annual_income: float | None = Field(default=None, ge=0)
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    existing_insurance_details: dict[str, Any] | None = None
    medical_history: dict[str, Any] | None = None
    additional_answers: dict[str, Any] | None = None
    form_step: str | None = None
    is_form_completed: bool = False


class InsuranceDetailUpdateRequest(BaseModel):
    """Request body for updating a transaction-linked insurance detail."""

    proposer_first_name: str | None = None
    proposer_last_name: str | None = None
    proposer_mobile_number: str | None = None
    proposer_email: str | None = None
    proposer_dob: date | None = None
    proposer_gender: str | None = None
    insured_members: list[dict[str, Any]] | None = None
    sum_insured_requested: float | None = Field(default=None, ge=0)
    policy_term_years: int | None = Field(default=None, ge=1)
    premium_preference: str | None = None
    occupation: str | None = None
    annual_income: float | None = Field(default=None, ge=0)
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    existing_insurance_details: dict[str, Any] | None = None
    medical_history: dict[str, Any] | None = None
    additional_answers: dict[str, Any] | None = None
    form_step: str | None = None
    is_form_completed: bool | None = None


class JourneyStartResponse(BaseModel):
    """Response body returned after creating a new journey."""

    user_id: str
    transaction_id: str
    insurance_detail_id: str
    current_status: TransactionStatus
    form_step: str | None


class LatestIncompleteJourneyResponse(BaseModel):
    """Response body for the latest incomplete journey lookup."""

    user_id: str
    transaction_id: str
    current_status: TransactionStatus
    form_step: str | None
    insurance_type: InsuranceType
    last_active_at: datetime
    insurance_detail_id: str


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc)


def _as_str_id(value: ObjectId | str) -> str:
    """Convert an ObjectId-like value to string."""

    return str(value)


async def _get_or_create_user(
    mobile_number: str,
    first_name: str | None,
    last_name: str | None,
) -> UserModel:
    """Return an existing user by mobile number or create a new one."""

    engine = get_engine()
    user = await engine.find_one(UserModel, UserModel.mobile_number == mobile_number)
    if user is not None:
        updated = False
        if first_name and not user.first_name:
            user.first_name = first_name
            updated = True
        if last_name and not user.last_name:
            user.last_name = last_name
            updated = True
        if updated:
            user.updated_at = _utc_now()
            await engine.save(user)
        return user

    user = UserModel(
        mobile_number=mobile_number,
        first_name=first_name or "Guest",
        last_name=last_name or "User",
    )
    await engine.save(user)
    return user


@router.post(
    "/journeys/start",
    response_model=JourneyStartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_journey(payload: JourneyStartRequest) -> JourneyStartResponse:
    """Create a new transaction and its linked insurance-detail snapshot."""

    try:
        engine = get_engine()
        user = await _get_or_create_user(
            mobile_number=payload.mobile_number,
            first_name=payload.proposer_first_name,
            last_name=payload.proposer_last_name,
        )

        transaction = TransactionModel(user_id=_as_str_id(user.id))
        await engine.save(transaction)

        insurance_detail = InsuranceDetailModel(
            transaction_id=transaction.transaction_id,
            user_id=_as_str_id(user.id),
            insurance_type=payload.insurance_type,
            proposer_first_name=payload.proposer_first_name,
            proposer_last_name=payload.proposer_last_name,
            proposer_mobile_number=payload.mobile_number,
            proposer_email=payload.proposer_email,
            proposer_dob=payload.proposer_dob,
            proposer_gender=payload.proposer_gender,
            insured_members=payload.insured_members,
            sum_insured_requested=payload.sum_insured_requested,
            policy_term_years=payload.policy_term_years,
            premium_preference=payload.premium_preference,
            occupation=payload.occupation,
            annual_income=payload.annual_income,
            city=payload.city,
            state=payload.state,
            postal_code=payload.postal_code,
            existing_insurance_details=payload.existing_insurance_details,
            medical_history=payload.medical_history,
            additional_answers=payload.additional_answers,
            form_step=payload.form_step,
            is_form_completed=payload.is_form_completed,
        )
        await engine.save(insurance_detail)

        user.updated_at = _utc_now()
        await engine.save(user)

        return JourneyStartResponse(
            user_id=_as_str_id(user.id),
            transaction_id=transaction.transaction_id,
            insurance_detail_id=_as_str_id(insurance_detail.id),
            current_status=transaction.current_status,
            form_step=insurance_detail.form_step,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start journey: {exc}",
        ) from exc


@router.patch(
    "/journeys/{transaction_id}/insurance-details",
    response_model=JourneyStartResponse,
)
async def update_insurance_detail(
    transaction_id: str,
    payload: InsuranceDetailUpdateRequest,
) -> JourneyStartResponse:
    """Update the insurance detail and transaction activity for a journey."""

    try:
        engine = get_engine()
        transaction = await engine.find_one(
            TransactionModel,
            TransactionModel.transaction_id == transaction_id,
        )
        if transaction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found",
            )

        insurance_detail = await engine.find_one(
            InsuranceDetailModel,
            InsuranceDetailModel.transaction_id == transaction_id,
        )
        if insurance_detail is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance detail not found for this transaction",
            )

        update_data = payload.model_dump(exclude_unset=True)
        for field_name, field_value in update_data.items():
            setattr(insurance_detail, field_name, field_value)

        insurance_detail.updated_at = _utc_now()
        transaction.last_active_at = _utc_now()
        transaction.updated_at = _utc_now()

        if insurance_detail.is_form_completed:
            transaction.current_status = TransactionStatus.FORM_SUBMITTED
            transaction.status_history.append(
                {"status": TransactionStatus.FORM_SUBMITTED, "timestamp": _utc_now()}
            )

        await engine.save(insurance_detail)
        await engine.save(transaction)

        return JourneyStartResponse(
            user_id=insurance_detail.user_id,
            transaction_id=transaction.transaction_id,
            insurance_detail_id=_as_str_id(insurance_detail.id),
            current_status=transaction.current_status,
            form_step=insurance_detail.form_step,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update insurance detail: {exc}",
        ) from exc


@router.get(
    "/users/{mobile_number}/latest-incomplete-journey",
    response_model=LatestIncompleteJourneyResponse,
)
async def get_latest_incomplete_journey(
    mobile_number: str,
) -> LatestIncompleteJourneyResponse:
    """Return the latest incomplete transaction for a user mobile number."""

    try:
        engine = get_engine()
        user = await engine.find_one(UserModel, UserModel.mobile_number == mobile_number)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        transactions = await engine.find(
            TransactionModel,
            TransactionModel.user_id == _as_str_id(user.id),
        )
        incomplete_transactions = [
            transaction
            for transaction in transactions
            if transaction.completed_at is None
            and transaction.current_status != TransactionStatus.PURCHASED
        ]
        if not incomplete_transactions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No incomplete journey found for this user",
            )

        latest_transaction = max(
            incomplete_transactions,
            key=lambda item: item.last_active_at,
        )
        insurance_detail = await engine.find_one(
            InsuranceDetailModel,
            InsuranceDetailModel.transaction_id == latest_transaction.transaction_id,
        )
        if insurance_detail is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance detail not found for latest incomplete journey",
            )

        return LatestIncompleteJourneyResponse(
            user_id=_as_str_id(user.id),
            transaction_id=latest_transaction.transaction_id,
            current_status=latest_transaction.current_status,
            form_step=insurance_detail.form_step,
            insurance_type=insurance_detail.insurance_type,
            last_active_at=latest_transaction.last_active_at,
            insurance_detail_id=_as_str_id(insurance_detail.id),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch latest incomplete journey: {exc}",
        ) from exc

"""Controller logic for insurance-detail journey flows in the main backend."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status

from commons.logger import logger
from core.apis.schemas.request_schema.insurance_detail_request_schema import (
    InsuranceDetailCreateRequest,
    InsuranceDetailUpdateRequest,
)
from core.apis.schemas.response_schema.insurance_detail_response_schema import (
    InsuranceDetailCreateResponse,
    InsuranceDetailUpdateResponse,
    LatestIncompleteInsuranceDetailResponse,
)
from core.cruds.insurance_detail_crud import InsuranceDetailCrud
from core.cruds.transaction_crud import TransactionCrud
from core.cruds.user_crud import UserCrud
from core.models.insurance_detail_model import InsuranceDetailModel
from core.models.transaction_model import TransactionModel, TransactionStatus
from core.models.user_model import UserModel
from core.services.provider_service import ProviderService

logging = logger(__name__)


class InsuranceDetailController:
    """Handles transaction-linked insurance form logic."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependencies."""

        self.user_crud = UserCrud()
        self.transaction_crud = TransactionCrud()
        self.insurance_detail_crud = InsuranceDetailCrud()
        self.provider_service = ProviderService()

    async def create_insurance_detail_journey(
        self,
        payload: InsuranceDetailCreateRequest,
    ) -> InsuranceDetailCreateResponse:
        """Create or find a user, create a transaction, and save insurance detail."""
        try:
            logging.info(
                "Executing InsuranceDetailController.create_insurance_detail_journey function"
            )
            normalized_mobile_number = payload.mobile_number.strip()
            user = await self.user_crud.get_by_mobile_number(normalized_mobile_number)
            if user is None:
                user = await self.user_crud.create(
                    UserModel.model_validate(
                        {
                            "mobile_number": normalized_mobile_number,
                            "first_name": payload.proposer_first_name or "Guest",
                            "last_name": payload.proposer_last_name or "User",
                        }
                    )
                )

            transaction = await self.transaction_crud.create(
                TransactionModel.model_validate({"user_id": str(user.id)})
            )
            insurance_detail = await self.insurance_detail_crud.create(
                InsuranceDetailModel.model_validate(
                    {
                        "transaction_id": transaction.transaction_id,
                        "user_id": str(user.id),
                        "insurance_type": payload.insurance_type,
                        "proposer_first_name": payload.proposer_first_name,
                        "proposer_last_name": payload.proposer_last_name,
                        "proposer_mobile_number": normalized_mobile_number,
                        "proposer_email": payload.proposer_email,
                        "proposer_dob": payload.proposer_dob,
                        "proposer_gender": payload.proposer_gender,
                        "insured_members": payload.insured_members,
                        "sum_insured_requested": payload.sum_insured_requested,
                        "policy_term_years": payload.policy_term_years,
                        "premium_preference": payload.premium_preference,
                        "occupation": payload.occupation,
                        "annual_income": payload.annual_income,
                        "city": payload.city,
                        "state": payload.state,
                        "postal_code": payload.postal_code,
                        "existing_insurance_details": payload.existing_insurance_details,
                        "medical_history": payload.medical_history,
                        "additional_answers": payload.additional_answers,
                        "form_step": payload.form_step,
                        "is_form_completed": payload.is_form_completed,
                    }
                )
            )
            if insurance_detail.is_form_completed:
                await self._generate_quotes_for_transaction(transaction, insurance_detail)

            logging.info(
                "Insurance-detail journey created successfully for transaction %s",
                transaction.transaction_id,
            )
            return InsuranceDetailCreateResponse(
                user_id=str(user.id),
                transaction_id=transaction.transaction_id,
                insurance_detail_id=str(insurance_detail.id),
                current_status=transaction.current_status,
                form_step=insurance_detail.form_step,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in InsuranceDetailController.create_insurance_detail_journey function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in InsuranceDetailController.create_insurance_detail_journey function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create insurance-detail journey.",
            )

    async def update_insurance_detail(
        self,
        transaction_id: str,
        payload: InsuranceDetailUpdateRequest,
    ) -> InsuranceDetailUpdateResponse:
        """Update a transaction-linked insurance-detail snapshot."""
        try:
            logging.info(
                "Executing InsuranceDetailController.update_insurance_detail function"
            )
            transaction = await self.transaction_crud.get_by_transaction_id(transaction_id)
            if transaction is None:
                logging.warning("Transaction not found for id %s", transaction_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )

            insurance_detail = await self.insurance_detail_crud.get_by_transaction_id(
                transaction_id
            )
            if insurance_detail is None:
                logging.warning(
                    "Insurance detail not found for transaction %s", transaction_id
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insurance detail not found for this transaction.",
                )

            update_data = payload.model_dump(exclude_unset=True)
            insurance_detail = await self.insurance_detail_crud.update(
                insurance_detail,
                update_data,
            )

            now = datetime.now(timezone.utc)
            transaction.last_active_at = now
            transaction.updated_at = now
            transaction = await self.transaction_crud.save(transaction)
            if insurance_detail.is_form_completed:
                await self._generate_quotes_for_transaction(transaction, insurance_detail)
            logging.info(
                "Insurance detail updated successfully for transaction %s",
                transaction_id,
            )
            return InsuranceDetailUpdateResponse(
                message="Insurance detail updated successfully.",
                transaction_id=transaction.transaction_id,
                insurance_detail_id=str(insurance_detail.id),
                current_status=transaction.current_status,
                form_step=insurance_detail.form_step,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in InsuranceDetailController.update_insurance_detail function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in InsuranceDetailController.update_insurance_detail function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update insurance detail.",
            )

    async def get_latest_incomplete_journey(
        self,
        mobile_number: str,
    ) -> LatestIncompleteInsuranceDetailResponse:
        """Return the latest incomplete journey for one mobile number."""
        try:
            logging.info(
                "Executing InsuranceDetailController.get_latest_incomplete_journey function"
            )
            normalized_mobile_number = mobile_number.strip()
            user = await self.user_crud.get_by_mobile_number(normalized_mobile_number)
            if user is None:
                logging.warning(
                    "User not found for mobile number %s", normalized_mobile_number
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )

            transaction = await self.transaction_crud.get_latest_incomplete_by_user_id(
                str(user.id)
            )
            if transaction is None:
                logging.warning(
                    "No incomplete journey found for user id %s", str(user.id)
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No incomplete journey found for this user.",
                )

            insurance_detail = await self.insurance_detail_crud.get_by_transaction_id(
                transaction.transaction_id
            )
            if insurance_detail is None:
                logging.warning(
                    "Insurance detail not found for latest incomplete transaction %s",
                    transaction.transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insurance detail not found for the latest incomplete journey.",
                )

            return LatestIncompleteInsuranceDetailResponse(
                user_id=str(user.id),
                transaction_id=transaction.transaction_id,
                current_status=transaction.current_status,
                form_step=insurance_detail.form_step,
                insurance_type=insurance_detail.insurance_type,
                last_active_at=transaction.last_active_at,
                insurance_detail_id=str(insurance_detail.id),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in InsuranceDetailController.get_latest_incomplete_journey function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in InsuranceDetailController.get_latest_incomplete_journey function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch latest incomplete journey.",
            )

    async def _generate_quotes_for_transaction(
        self,
        transaction: TransactionModel,
        insurance_detail: InsuranceDetailModel,
    ) -> None:
        """Trigger provider quote generation and update transaction status."""

        if transaction.current_status != TransactionStatus.FORM_SUBMITTED:
            return

        await self.provider_service.generate_quotes(
            {
                "transaction_id": transaction.transaction_id,
                "user_id": insurance_detail.user_id,
                "insurance_type": insurance_detail.insurance_type.value,
                "proposer_dob": (
                    insurance_detail.proposer_dob.isoformat()
                    if insurance_detail.proposer_dob is not None
                    else None
                ),
                "proposer_gender": insurance_detail.proposer_gender,
                "city": insurance_detail.city,
                "state": insurance_detail.state,
                "sum_insured_requested": insurance_detail.sum_insured_requested,
                "policy_term_years": insurance_detail.policy_term_years,
                "occupation": insurance_detail.occupation,
                "annual_income": insurance_detail.annual_income,
                "medical_history": insurance_detail.medical_history,
                "additional_answers": insurance_detail.additional_answers,
            }
        )
        await self.transaction_crud.update_status(
            transaction,
            TransactionStatus.OFFERS_RECEIVED,
        )

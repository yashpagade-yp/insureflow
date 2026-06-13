"""Controller logic for transaction reads and quote-selection status updates."""

from __future__ import annotations

from fastapi import HTTPException, status

from ...commons.logger import logger
from ..apis.schemas.request_schema.quote_request_schema import (
    QuoteSelectAddOnsRequest,
    QuoteSelectPlanRequest,
)
from ..apis.schemas.response_schema.transaction_response_schema import (
    TransactionListResponse,
    TransactionResponse,
)
from ..cruds.transaction_crud import TransactionCrud
from ..models.transaction_model import TransactionModel, TransactionStatus

logging = logger(__name__)


class TransactionController:
    """Handles transaction read and update business logic."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependency."""

        self.transaction_crud = TransactionCrud()

    async def get_transaction(self, transaction_id: str) -> TransactionResponse:
        """Return one transaction by business transaction id."""
        try:
            logging.info("Executing TransactionController.get_transaction")
            transaction = await self.transaction_crud.get_by_transaction_id(transaction_id)
            if transaction is None:
                logging.warning("Transaction not found for id %s", transaction_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )
            return self._build_response(transaction)
        except HTTPException:
            raise
        except Exception as error:
            logging.error("Error in TransactionController.get_transaction: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch transaction.",
            )

    async def list_user_transactions(self, user_id: str) -> TransactionListResponse:
        """Return all transactions for one user."""
        try:
            logging.info("Executing TransactionController.list_user_transactions")
            transactions = await self.transaction_crud.list_by_user_id(user_id)
            return TransactionListResponse(
                items=[self._build_response(item) for item in transactions],
                total_count=len(transactions),
            )
        except HTTPException:
            raise
        except Exception as error:
            logging.error(
                "Error in TransactionController.list_user_transactions: %s", error
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list user transactions.",
            )

    async def select_plan(self, payload: QuoteSelectPlanRequest) -> TransactionResponse:
        """Save the selected provider plan on a transaction."""
        try:
            logging.info("Executing TransactionController.select_plan")
            transaction = await self.transaction_crud.get_by_transaction_id(
                payload.transaction_id
            )
            if transaction is None:
                logging.warning(
                    "Transaction not found for id %s during plan selection",
                    payload.transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )

            transaction = await self.transaction_crud.set_selected_plan_id(
                transaction,
                payload.selected_plan_id,
            )
            transaction = await self.transaction_crud.update_status(
                transaction,
                TransactionStatus.OFFER_SELECTED,
            )
            return self._build_response(transaction)
        except HTTPException:
            raise
        except Exception as error:
            logging.error("Error in TransactionController.select_plan: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to select transaction plan.",
            )

    async def save_selected_add_ons(
        self,
        payload: QuoteSelectAddOnsRequest,
    ) -> TransactionResponse:
        """Move the transaction to add-on selected state."""
        try:
            logging.info("Executing TransactionController.save_selected_add_ons")
            transaction = await self.transaction_crud.get_by_transaction_id(
                payload.transaction_id
            )
            if transaction is None:
                logging.warning(
                    "Transaction not found for id %s during add-on selection",
                    payload.transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )

            if transaction.selected_plan_id != payload.selected_plan_id:
                transaction = await self.transaction_crud.set_selected_plan_id(
                    transaction,
                    payload.selected_plan_id,
                )

            transaction = await self.transaction_crud.update_status(
                transaction,
                TransactionStatus.ADD_ONS_SELECTED,
            )
            return self._build_response(transaction)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(
                "Error in TransactionController.save_selected_add_ons: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save selected add-ons for transaction.",
            )

    def _build_response(self, transaction: TransactionModel) -> TransactionResponse:
        """Convert a transaction document into the public response schema."""

        return TransactionResponse(
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            current_status=transaction.current_status,
            selected_plan_id=transaction.selected_plan_id,
            last_active_at=transaction.last_active_at,
            completed_at=transaction.completed_at,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
        )

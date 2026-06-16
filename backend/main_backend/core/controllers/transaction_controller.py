"""Controller logic for transaction reads and quote-selection status updates."""

from __future__ import annotations

from fastapi import HTTPException, status

from commons.logger import logger
from core.apis.schemas.request_schema.quote_request_schema import (
    QuoteSelectAddOnsRequest,
    QuoteSelectPlanRequest,
)
from core.apis.schemas.response_schema.transaction_response_schema import (
    TransactionListResponse,
    TransactionResponse,
)
from core.cruds.transaction_crud import TransactionCrud
from core.models.transaction_model import TransactionModel, TransactionStatus
from core.services.provider_service import ProviderService

logging = logger(__name__)


class TransactionController:
    """Handles transaction read and update business logic."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependency."""

        self.transaction_crud = TransactionCrud()
        self.provider_service = ProviderService()

    async def get_transaction(self, transaction_id: str) -> TransactionResponse:
        """Return one transaction by business transaction id.

        Args:
            transaction_id: Business transaction identifier to look up.

        Returns:
            TransactionResponse: Serialized transaction details.

        Raises:
            HTTPException: If the transaction identifier is invalid or the
                transaction cannot be found.
        """
        try:
            logging.info("Executing TransactionController.get_transaction function")
            normalized_transaction_id = transaction_id.strip()
            if not normalized_transaction_id:
                logging.warning("Empty transaction_id provided for transaction lookup")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction id is required.",
                )

            transaction = await self.transaction_crud.get_by_transaction_id(
                normalized_transaction_id
            )
            if transaction is None:
                logging.warning(
                    "Transaction not found for id %s",
                    normalized_transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )
            return self._build_response(transaction)
        except HTTPException as httperror:
            logging.error(
                "Error in TransactionController.get_transaction function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in TransactionController.get_transaction function: %s", error
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch transaction.",
            )

    async def list_user_transactions(self, user_id: str) -> TransactionListResponse:
        """Return all transactions for one user.

        Args:
            user_id: User identifier whose transactions should be returned.

        Returns:
            TransactionListResponse: Ordered list of transactions for the user.

        Raises:
            HTTPException: If the user identifier is invalid or the transactions
                cannot be listed.
        """
        try:
            logging.info(
                "Executing TransactionController.list_user_transactions function"
            )
            normalized_user_id = user_id.strip()
            if not normalized_user_id:
                logging.warning("Empty user_id provided for transaction listing")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User id is required.",
                )

            transactions = await self.transaction_crud.list_by_user_id(normalized_user_id)
            return TransactionListResponse(
                items=[self._build_response(item) for item in transactions],
                total_count=len(transactions),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in TransactionController.list_user_transactions function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in TransactionController.list_user_transactions function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list user transactions.",
            )

    async def list_all_transactions(self) -> TransactionListResponse:
        """Return all transactions for the admin dashboard.

        Returns:
            TransactionListResponse: Ordered list of all transactions.

        Raises:
            HTTPException: If transaction listing fails.
        """

        try:
            logging.info("Executing TransactionController.list_all_transactions function")
            transactions = await self.transaction_crud.list_all()
            return TransactionListResponse(
                items=[self._build_response(item) for item in transactions],
                total_count=len(transactions),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in TransactionController.list_all_transactions function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in TransactionController.list_all_transactions function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list transactions.",
            )

    async def list_pending_forms(self) -> TransactionListResponse:
        """Return all incomplete transactions for pending-form monitoring."""

        try:
            logging.info("Executing TransactionController.list_pending_forms function")
            transactions = await self.transaction_crud.list_incomplete()
            return TransactionListResponse(
                items=[self._build_response(item) for item in transactions],
                total_count=len(transactions),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in TransactionController.list_pending_forms function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in TransactionController.list_pending_forms function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list pending forms.",
            )

    async def list_completed_journeys(self) -> TransactionListResponse:
        """Return all purchased transactions for completed-journey monitoring."""

        try:
            logging.info(
                "Executing TransactionController.list_completed_journeys function"
            )
            transactions = await self.transaction_crud.list_completed()
            return TransactionListResponse(
                items=[self._build_response(item) for item in transactions],
                total_count=len(transactions),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in TransactionController.list_completed_journeys function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in TransactionController.list_completed_journeys function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list completed journeys.",
            )

    async def select_plan(self, payload: QuoteSelectPlanRequest) -> TransactionResponse:
        """Save the selected provider plan on a transaction.

        Args:
            payload: Transaction id and selected plan id from the quote flow.

        Returns:
            TransactionResponse: Updated transaction after plan selection.

        Raises:
            HTTPException: If the transaction or plan identifiers are invalid,
                or the transaction cannot be updated.
        """
        try:
            logging.info("Executing TransactionController.select_plan function")
            normalized_transaction_id = payload.transaction_id.strip()
            normalized_selected_plan_id = payload.selected_plan_id.strip()
            if not normalized_transaction_id or not normalized_selected_plan_id:
                logging.warning(
                    "Transaction plan selection received empty identifiers"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction id and selected plan id are required.",
                )

            transaction = await self.transaction_crud.get_by_transaction_id(
                normalized_transaction_id
            )
            if transaction is None:
                logging.warning(
                    "Transaction not found for id %s during plan selection",
                    normalized_transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )

            await self.provider_service.select_plan(
                normalized_transaction_id,
                normalized_selected_plan_id,
            )
            transaction = await self.transaction_crud.set_selected_plan_id(
                transaction,
                normalized_selected_plan_id,
            )
            transaction = await self.transaction_crud.update_status(
                transaction,
                TransactionStatus.OFFER_SELECTED,
            )
            return self._build_response(transaction)
        except HTTPException as httperror:
            logging.error(
                "Error in TransactionController.select_plan function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in TransactionController.select_plan function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to select transaction plan.",
            )

    async def save_selected_add_ons(
        self,
        payload: QuoteSelectAddOnsRequest,
    ) -> TransactionResponse:
        """Move the transaction to add-on selected state.

        Args:
            payload: Transaction id, selected plan id, and selected add-ons.

        Returns:
            TransactionResponse: Updated transaction after add-on selection.

        Raises:
            HTTPException: If the transaction or plan identifiers are invalid,
                or the add-on update cannot be completed.
        """
        try:
            logging.info(
                "Executing TransactionController.save_selected_add_ons function"
            )
            normalized_transaction_id = payload.transaction_id.strip()
            normalized_selected_plan_id = payload.selected_plan_id.strip()
            if not normalized_transaction_id or not normalized_selected_plan_id:
                logging.warning(
                    "Transaction add-on selection received empty identifiers"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction id and selected plan id are required.",
                )

            transaction = await self.transaction_crud.get_by_transaction_id(
                normalized_transaction_id
            )
            if transaction is None:
                logging.warning(
                    "Transaction not found for id %s during add-on selection",
                    normalized_transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )

            await self.provider_service.update_add_ons(
                normalized_transaction_id,
                normalized_selected_plan_id,
                [item.model_dump() for item in payload.selected_add_ons],
            )
            if transaction.selected_plan_id != normalized_selected_plan_id:
                transaction = await self.transaction_crud.set_selected_plan_id(
                    transaction,
                    normalized_selected_plan_id,
                )

            transaction = await self.transaction_crud.update_status(
                transaction,
                TransactionStatus.ADD_ONS_SELECTED,
            )
            return self._build_response(transaction)
        except HTTPException as httperror:
            logging.error(
                "Error in TransactionController.save_selected_add_ons function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in TransactionController.save_selected_add_ons function: %s",
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

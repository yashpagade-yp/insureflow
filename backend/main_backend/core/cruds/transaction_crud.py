"""CRUD helpers for transaction documents in the main backend."""

from __future__ import annotations

from datetime import datetime, timezone

from odmantic import ObjectId

from commons.logger import logger
from core.database.database import get_engine
from core.models.transaction_model import (
    StatusHistoryEntry,
    TransactionModel,
    TransactionStatus,
)

logging = logger(__name__)


class TransactionCrud:
    """Provides database operations for transaction documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, transaction: TransactionModel) -> TransactionModel:
        """Persist a new transaction document."""
        try:
            logging.info("Executing TransactionCrud.create function")
            await self.engine.save(transaction)
            return transaction
        except Exception as error:
            logging.error("Error in TransactionCrud.create function: %s", error)
            raise

    async def get_by_id(self, object_id: str | ObjectId) -> TransactionModel | None:
        """Return one transaction by ODMantic object id."""
        try:
            logging.info("Executing TransactionCrud.get_by_id function")
            if isinstance(object_id, str):
                if len(object_id) != 24:
                    return None
                object_id = ObjectId(object_id)
            return await self.engine.find_one(
                TransactionModel,
                TransactionModel.id == object_id,
            )
        except Exception as error:
            logging.error("Error in TransactionCrud.get_by_id function: %s", error)
            raise

    async def get_by_transaction_id(self, transaction_id: str) -> TransactionModel | None:
        """Return one transaction by business transaction id."""
        try:
            logging.info("Executing TransactionCrud.get_by_transaction_id function")
            return await self.engine.find_one(
                TransactionModel,
                TransactionModel.transaction_id == transaction_id,
            )
        except Exception as error:
            logging.error(
                "Error in TransactionCrud.get_by_transaction_id function: %s", error
            )
            raise

    async def list_by_user_id(self, user_id: str) -> list[TransactionModel]:
        """Return all transactions for a user, newest first."""
        try:
            logging.info("Executing TransactionCrud.list_by_user_id function")
            transactions = await self.engine.find(
                TransactionModel,
                TransactionModel.user_id == user_id,
            )
            return sorted(transactions, key=lambda item: item.updated_at, reverse=True)
        except Exception as error:
            logging.error(
                "Error in TransactionCrud.list_by_user_id function: %s", error
            )
            raise

    async def get_latest_incomplete_by_user_id(self, user_id: str) -> TransactionModel | None:
        """Return the latest transaction that has not been fully purchased."""
        try:
            logging.info(
                "Executing TransactionCrud.get_latest_incomplete_by_user_id function"
            )
            transactions = await self.list_by_user_id(user_id)
            for transaction in transactions:
                if transaction.current_status != TransactionStatus.PURCHASED:
                    return transaction
            return None
        except Exception as error:
            logging.error(
                "Error in TransactionCrud.get_latest_incomplete_by_user_id function: %s",
                error,
            )
            raise

    async def save(self, transaction: TransactionModel) -> TransactionModel:
        """Persist an already-mutated transaction document."""
        try:
            logging.info("Executing TransactionCrud.save function")
            transaction.updated_at = datetime.now(timezone.utc)
            await self.engine.save(transaction)
            return transaction
        except Exception as error:
            logging.error("Error in TransactionCrud.save function: %s", error)
            raise

    async def update_status(
        self,
        transaction: TransactionModel,
        status: TransactionStatus,
    ) -> TransactionModel:
        """Update the current status and append one history entry."""
        try:
            logging.info("Executing TransactionCrud.update_status function")
            now = datetime.now(timezone.utc)
            transaction.current_status = status
            transaction.last_active_at = now
            transaction.updated_at = now
            transaction.status_history.append(
                StatusHistoryEntry(status=status, timestamp=now)
            )
            if status == TransactionStatus.PURCHASED:
                transaction.completed_at = now

            await self.engine.save(transaction)
            return transaction
        except Exception as error:
            logging.error("Error in TransactionCrud.update_status function: %s", error)
            raise

    async def set_selected_plan_id(
        self,
        transaction: TransactionModel,
        selected_plan_id: str,
    ) -> TransactionModel:
        """Save the selected provider plan identifier on a transaction."""
        try:
            logging.info("Executing TransactionCrud.set_selected_plan_id function")
            now = datetime.now(timezone.utc)
            transaction.selected_plan_id = selected_plan_id
            transaction.last_active_at = now
            transaction.updated_at = now
            await self.engine.save(transaction)
            return transaction
        except Exception as error:
            logging.error(
                "Error in TransactionCrud.set_selected_plan_id function: %s", error
            )
            raise

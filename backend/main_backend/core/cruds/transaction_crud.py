"""CRUD helpers for transaction documents in the main backend."""

from __future__ import annotations

from datetime import datetime, timezone

from odmantic import ObjectId

from ..database.database import get_engine
from ..models.transaction_model import (
    StatusHistoryEntry,
    TransactionModel,
    TransactionStatus,
)


class TransactionCrud:
    """Provides database operations for transaction documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, transaction: TransactionModel) -> TransactionModel:
        """Persist a new transaction document."""

        await self.engine.save(transaction)
        return transaction

    async def get_by_id(self, object_id: str | ObjectId) -> TransactionModel | None:
        """Return one transaction by ODMantic object id."""

        return await self.engine.find_one(TransactionModel, TransactionModel.id == object_id)

    async def get_by_transaction_id(self, transaction_id: str) -> TransactionModel | None:
        """Return one transaction by business transaction id."""

        return await self.engine.find_one(
            TransactionModel,
            TransactionModel.transaction_id == transaction_id,
        )

    async def list_by_user_id(self, user_id: str) -> list[TransactionModel]:
        """Return all transactions for a user, newest first."""

        transactions = await self.engine.find(
            TransactionModel,
            TransactionModel.user_id == user_id,
        )
        return sorted(transactions, key=lambda item: item.updated_at, reverse=True)

    async def get_latest_incomplete_by_user_id(self, user_id: str) -> TransactionModel | None:
        """Return the latest transaction that has not been fully purchased."""

        transactions = await self.list_by_user_id(user_id)
        for transaction in transactions:
            if transaction.current_status != TransactionStatus.PURCHASED:
                return transaction
        return None

    async def save(self, transaction: TransactionModel) -> TransactionModel:
        """Persist an already-mutated transaction document."""

        transaction.updated_at = datetime.now(timezone.utc)
        await self.engine.save(transaction)
        return transaction

    async def update_status(
        self,
        transaction: TransactionModel,
        status: TransactionStatus,
    ) -> TransactionModel:
        """Update the current status and append one history entry."""

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

    async def set_selected_plan_id(
        self,
        transaction: TransactionModel,
        selected_plan_id: str,
    ) -> TransactionModel:
        """Save the selected provider plan identifier on a transaction."""

        now = datetime.now(timezone.utc)
        transaction.selected_plan_id = selected_plan_id
        transaction.last_active_at = now
        transaction.updated_at = now
        await self.engine.save(transaction)
        return transaction

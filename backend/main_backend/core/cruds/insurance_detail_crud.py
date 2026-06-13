"""CRUD helpers for insurance-detail documents in the main backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from odmantic import ObjectId

from commons.logger import logger
from core.database.database import get_engine
from core.models.insurance_detail_model import InsuranceDetailModel

logging = logger(__name__)


class InsuranceDetailCrud:
    """Provides database operations for insurance-detail documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, insurance_detail: InsuranceDetailModel) -> InsuranceDetailModel:
        """Persist a new insurance-detail document."""
        try:
            logging.info("Executing InsuranceDetailCrud.create function")
            await self.engine.save(insurance_detail)
            return insurance_detail
        except Exception as error:
            logging.error("Error in InsuranceDetailCrud.create function: %s", error)
            raise

    async def get_by_id(
        self,
        object_id: str | ObjectId,
    ) -> InsuranceDetailModel | None:
        """Return one insurance-detail document by ODMantic object id."""
        try:
            logging.info("Executing InsuranceDetailCrud.get_by_id function")
            if isinstance(object_id, str):
                if len(object_id) != 24:
                    return None
                object_id = ObjectId(object_id)
            return await self.engine.find_one(
                InsuranceDetailModel,
                InsuranceDetailModel.id == object_id,
            )
        except Exception as error:
            logging.error("Error in InsuranceDetailCrud.get_by_id function: %s", error)
            raise

    async def get_by_transaction_id(
        self,
        transaction_id: str,
    ) -> InsuranceDetailModel | None:
        """Return one insurance-detail document by transaction id."""
        try:
            logging.info("Executing InsuranceDetailCrud.get_by_transaction_id function")
            return await self.engine.find_one(
                InsuranceDetailModel,
                InsuranceDetailModel.transaction_id == transaction_id,
            )
        except Exception as error:
            logging.error(
                "Error in InsuranceDetailCrud.get_by_transaction_id function: %s",
                error,
            )
            raise

    async def get_by_user_id(self, user_id: str) -> list[InsuranceDetailModel]:
        """Return all insurance-detail documents for one user."""
        try:
            logging.info("Executing InsuranceDetailCrud.get_by_user_id function")
            items = await self.engine.find(
                InsuranceDetailModel,
                InsuranceDetailModel.user_id == user_id,
            )
            return sorted(items, key=lambda item: item.updated_at, reverse=True)
        except Exception as error:
            logging.error(
                "Error in InsuranceDetailCrud.get_by_user_id function: %s", error
            )
            raise

    async def update(
        self,
        insurance_detail: InsuranceDetailModel,
        updates: dict[str, Any],
    ) -> InsuranceDetailModel:
        """Apply partial updates to an insurance-detail document and save it."""
        try:
            logging.info("Executing InsuranceDetailCrud.update function")
            for field_name, field_value in updates.items():
                setattr(insurance_detail, field_name, field_value)

            insurance_detail.updated_at = datetime.now(timezone.utc)
            await self.engine.save(insurance_detail)
            return insurance_detail
        except Exception as error:
            logging.error("Error in InsuranceDetailCrud.update function: %s", error)
            raise

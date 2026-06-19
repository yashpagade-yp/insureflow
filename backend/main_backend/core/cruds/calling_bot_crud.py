"""CRUD helpers for calling-bot call records in the main backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from commons.logger import logger
from core.database.database import get_engine
from core.models.calling_bot_model import CallingBotCallModel

logging = logger(__name__)


class CallingBotCrud:
    """Provides persistence helpers for calling-bot call documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, call_record: CallingBotCallModel) -> CallingBotCallModel:
        """Persist a new calling-bot call document."""

        try:
            logging.info("Executing CallingBotCrud.create function")
            await self.engine.save(call_record)
            return call_record
        except Exception as error:
            logging.error("Error in CallingBotCrud.create function: %s", error)
            raise

    async def get_by_call_reference(self, call_reference: str) -> CallingBotCallModel | None:
        """Return one call document by internal call reference."""

        try:
            logging.info("Executing CallingBotCrud.get_by_call_reference function")
            return await self.engine.find_one(
                CallingBotCallModel,
                CallingBotCallModel.call_reference == call_reference,
            )
        except Exception as error:
            logging.error("Error in CallingBotCrud.get_by_call_reference function: %s", error)
            raise

    async def list_all(self) -> list[CallingBotCallModel]:
        """Return all call documents ordered by newest first."""

        try:
            logging.info("Executing CallingBotCrud.list_all function")
            items = await self.engine.find(CallingBotCallModel)
            return sorted(items, key=lambda item: item.updated_at, reverse=True)
        except Exception as error:
            logging.error("Error in CallingBotCrud.list_all function: %s", error)
            raise

    async def update(
        self,
        call_record: CallingBotCallModel,
        updates: dict[str, Any],
    ) -> CallingBotCallModel:
        """Apply partial updates to one call document and persist it."""

        try:
            logging.info("Executing CallingBotCrud.update function")
            for field_name, field_value in updates.items():
                setattr(call_record, field_name, field_value)

            call_record.updated_at = datetime.now(timezone.utc)
            await self.engine.save(call_record)
            return call_record
        except Exception as error:
            logging.error("Error in CallingBotCrud.update function: %s", error)
            raise

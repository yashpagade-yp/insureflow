"""CRUD helpers for support-ticket documents in the main backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from odmantic import ObjectId

from commons.logger import logger
from core.database.database import get_engine
from core.models.ticket_model import TicketModel

logging = logger(__name__)


class TicketCrud:
    """Provides database operations for support-ticket documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, ticket: TicketModel) -> TicketModel:
        """Persist a new support-ticket document."""

        try:
            logging.info("Executing TicketCrud.create function")
            await self.engine.save(ticket)
            return ticket
        except Exception as error:
            logging.error("Error in TicketCrud.create function: %s", error)
            raise

    async def get_by_id(self, object_id: str | ObjectId) -> TicketModel | None:
        """Return one support ticket by ODMantic object id."""

        try:
            logging.info("Executing TicketCrud.get_by_id function")
            if isinstance(object_id, str):
                if len(object_id) != 24:
                    return None
                object_id = ObjectId(object_id)
            return await self.engine.find_one(TicketModel, TicketModel.id == object_id)
        except Exception as error:
            logging.error("Error in TicketCrud.get_by_id function: %s", error)
            raise

    async def get_by_ticket_id(self, ticket_id: str) -> TicketModel | None:
        """Return one support ticket by business ticket id."""

        try:
            logging.info("Executing TicketCrud.get_by_ticket_id function")
            return await self.engine.find_one(
                TicketModel,
                TicketModel.ticket_id == ticket_id,
            )
        except Exception as error:
            logging.error("Error in TicketCrud.get_by_ticket_id function: %s", error)
            raise

    async def list_by_user_id(self, user_id: str) -> list[TicketModel]:
        """Return all support tickets for one user, newest first."""

        try:
            logging.info("Executing TicketCrud.list_by_user_id function")
            tickets = await self.engine.find(TicketModel, TicketModel.user_id == user_id)
            return sorted(tickets, key=lambda item: item.updated_at, reverse=True)
        except Exception as error:
            logging.error("Error in TicketCrud.list_by_user_id function: %s", error)
            raise

    async def list_all(self) -> list[TicketModel]:
        """Return all support tickets, newest first."""

        try:
            logging.info("Executing TicketCrud.list_all function")
            tickets = await self.engine.find(TicketModel)
            return sorted(tickets, key=lambda item: item.updated_at, reverse=True)
        except Exception as error:
            logging.error("Error in TicketCrud.list_all function: %s", error)
            raise

    async def update(self, ticket: TicketModel, updates: dict[str, Any]) -> TicketModel:
        """Apply partial updates to a support ticket and save it."""

        try:
            logging.info("Executing TicketCrud.update function")
            for field_name, field_value in updates.items():
                setattr(ticket, field_name, field_value)

            ticket.updated_at = datetime.now(timezone.utc)
            await self.engine.save(ticket)
            return ticket
        except Exception as error:
            logging.error("Error in TicketCrud.update function: %s", error)
            raise

"""CRUD helpers for quote documents in the provider backend."""

from __future__ import annotations

from datetime import datetime, timezone

from commons.logger import logger
from core.database.database import get_engine
from core.models.quote_model import QuoteItem, QuoteModel, QuoteStatus, SelectedAddOn

logging = logger(__name__)


class QuoteCrud:
    """Provides database operations for provider quote documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, quote: QuoteModel) -> QuoteModel:
        """Persist a new quote document."""
        try:
            logging.info("Executing QuoteCrud.create function")
            await self.engine.save(quote)
            return quote
        except Exception as error:
            logging.error("Error in QuoteCrud.create function: %s", error)
            raise

    async def get_by_transaction_id(self, transaction_id: str) -> QuoteModel | None:
        """Return one quote document by transaction id."""
        try:
            logging.info("Executing QuoteCrud.get_by_transaction_id function")
            return await self.engine.find_one(
                QuoteModel,
                QuoteModel.transaction_id == transaction_id,
            )
        except Exception as error:
            logging.error("Error in QuoteCrud.get_by_transaction_id function: %s", error)
            raise

    async def list_all(self) -> list[QuoteModel]:
        """Return all quote documents, newest first."""
        try:
            logging.info("Executing QuoteCrud.list_all function")
            quotes = await self.engine.find(QuoteModel)
            return sorted(quotes, key=lambda item: item.updated_at, reverse=True)
        except Exception as error:
            logging.error("Error in QuoteCrud.list_all function: %s", error)
            raise

    async def save(self, quote: QuoteModel) -> QuoteModel:
        """Persist an already-mutated quote document."""
        try:
            logging.info("Executing QuoteCrud.save function")
            quote.updated_at = datetime.now(timezone.utc)
            await self.engine.save(quote)
            return quote
        except Exception as error:
            logging.error("Error in QuoteCrud.save function: %s", error)
            raise

    async def replace_items(
        self,
        quote: QuoteModel,
        items: list[QuoteItem],
    ) -> QuoteModel:
        """Replace all generated quote items for a transaction."""
        try:
            logging.info("Executing QuoteCrud.replace_items function")
            quote.items = items
            quote.updated_at = datetime.now(timezone.utc)
            await self.engine.save(quote)
            return quote
        except Exception as error:
            logging.error("Error in QuoteCrud.replace_items function: %s", error)
            raise

    async def set_selected_plan_id(self, quote: QuoteModel, selected_plan_id: str) -> QuoteModel:
        """Save the selected provider plan id on a quote document."""
        try:
            logging.info("Executing QuoteCrud.set_selected_plan_id function")
            quote.selected_plan_id = selected_plan_id
            quote.updated_at = datetime.now(timezone.utc)
            await self.engine.save(quote)
            return quote
        except Exception as error:
            logging.error("Error in QuoteCrud.set_selected_plan_id function: %s", error)
            raise

    async def set_selected_add_ons(
        self,
        quote: QuoteModel,
        plan_id: str,
        selected_add_ons: list[SelectedAddOn],
        add_on_total: float,
        tax_amount: float,
        total_premium: float,
    ) -> QuoteModel:
        """Update selected add-ons and totals for one embedded quote item."""
        try:
            logging.info("Executing QuoteCrud.set_selected_add_ons function")
            for item in quote.items:
                if item.plan_id == plan_id:
                    item.selected_add_ons = selected_add_ons
                    item.add_on_total = add_on_total
                    item.tax_amount = tax_amount
                    item.total_premium = total_premium
                    break

            quote.updated_at = datetime.now(timezone.utc)
            await self.engine.save(quote)
            return quote
        except Exception as error:
            logging.error("Error in QuoteCrud.set_selected_add_ons function: %s", error)
            raise

    async def update_item_status(
        self,
        quote: QuoteModel,
        plan_id: str,
        status: QuoteStatus,
    ) -> QuoteModel:
        """Update the status of one embedded quote item."""
        try:
            logging.info("Executing QuoteCrud.update_item_status function")
            for item in quote.items:
                if item.plan_id == plan_id:
                    item.quote_status = status
                    break

            quote.updated_at = datetime.now(timezone.utc)
            await self.engine.save(quote)
            return quote
        except Exception as error:
            logging.error("Error in QuoteCrud.update_item_status function: %s", error)
            raise

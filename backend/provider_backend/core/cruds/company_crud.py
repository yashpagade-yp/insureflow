"""CRUD helpers for company documents in the provider backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from odmantic import ObjectId

from ...commons.logger import logger
from ..database.database import get_engine
from ..models.company_model import CompanyModel

logging = logger(__name__)


class CompanyCrud:
    """Provides database operations for provider company documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, company: CompanyModel) -> CompanyModel:
        """Persist a new company document."""
        try:
            logging.info("Executing CompanyCrud.create function")
            await self.engine.save(company)
            return company
        except Exception as error:
            logging.error("Error in CompanyCrud.create function: %s", error)
            raise

    async def get_by_id(self, object_id: str | ObjectId) -> CompanyModel | None:
        """Return one company by ODMantic object id."""
        try:
            logging.info("Executing CompanyCrud.get_by_id function")
            return await self.engine.find_one(CompanyModel, CompanyModel.id == object_id)
        except Exception as error:
            logging.error("Error in CompanyCrud.get_by_id function: %s", error)
            raise

    async def get_by_company_name(self, company_name: str) -> CompanyModel | None:
        """Return one company by unique company name."""
        try:
            logging.info("Executing CompanyCrud.get_by_company_name function")
            return await self.engine.find_one(
                CompanyModel,
                CompanyModel.company_name == company_name,
            )
        except Exception as error:
            logging.error("Error in CompanyCrud.get_by_company_name function: %s", error)
            raise

    async def list_all(self) -> list[CompanyModel]:
        """Return all companies, newest first."""
        try:
            logging.info("Executing CompanyCrud.list_all function")
            companies = await self.engine.find(CompanyModel)
            return sorted(companies, key=lambda item: item.created_at, reverse=True)
        except Exception as error:
            logging.error("Error in CompanyCrud.list_all function: %s", error)
            raise

    async def update(self, company: CompanyModel, updates: dict[str, Any]) -> CompanyModel:
        """Apply partial updates to a company document and save it."""
        try:
            logging.info("Executing CompanyCrud.update function")
            for field_name, field_value in updates.items():
                setattr(company, field_name, field_value)

            company.updated_at = datetime.now(timezone.utc)
            await self.engine.save(company)
            return company
        except Exception as error:
            logging.error("Error in CompanyCrud.update function: %s", error)
            raise

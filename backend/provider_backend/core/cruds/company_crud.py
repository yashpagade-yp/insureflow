"""CRUD helpers for company documents in the provider backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from odmantic import ObjectId

from ..database.database import get_engine
from ..models.company_model import CompanyModel


class CompanyCrud:
    """Provides database operations for provider company documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, company: CompanyModel) -> CompanyModel:
        """Persist a new company document."""

        await self.engine.save(company)
        return company

    async def get_by_id(self, object_id: str | ObjectId) -> CompanyModel | None:
        """Return one company by ODMantic object id."""

        return await self.engine.find_one(CompanyModel, CompanyModel.id == object_id)

    async def get_by_company_name(self, company_name: str) -> CompanyModel | None:
        """Return one company by unique company name."""

        return await self.engine.find_one(
            CompanyModel,
            CompanyModel.company_name == company_name,
        )

    async def list_all(self) -> list[CompanyModel]:
        """Return all companies, newest first."""

        companies = await self.engine.find(CompanyModel)
        return sorted(companies, key=lambda item: item.created_at, reverse=True)

    async def update(self, company: CompanyModel, updates: dict[str, Any]) -> CompanyModel:
        """Apply partial updates to a company document and save it."""

        for field_name, field_value in updates.items():
            setattr(company, field_name, field_value)

        company.updated_at = datetime.now(timezone.utc)
        await self.engine.save(company)
        return company

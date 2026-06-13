"""CRUD helpers for insurance-detail documents in the main backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from odmantic import ObjectId

from ..database.database import get_engine
from ..models.insurance_detail_model import InsuranceDetailModel


class InsuranceDetailCrud:
    """Provides database operations for insurance-detail documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, insurance_detail: InsuranceDetailModel) -> InsuranceDetailModel:
        """Persist a new insurance-detail document."""

        await self.engine.save(insurance_detail)
        return insurance_detail

    async def get_by_id(
        self,
        object_id: str | ObjectId,
    ) -> InsuranceDetailModel | None:
        """Return one insurance-detail document by ODMantic object id."""

        return await self.engine.find_one(
            InsuranceDetailModel,
            InsuranceDetailModel.id == object_id,
        )

    async def get_by_transaction_id(
        self,
        transaction_id: str,
    ) -> InsuranceDetailModel | None:
        """Return one insurance-detail document by transaction id."""

        return await self.engine.find_one(
            InsuranceDetailModel,
            InsuranceDetailModel.transaction_id == transaction_id,
        )

    async def get_by_user_id(self, user_id: str) -> list[InsuranceDetailModel]:
        """Return all insurance-detail documents for one user."""

        items = await self.engine.find(
            InsuranceDetailModel,
            InsuranceDetailModel.user_id == user_id,
        )
        return sorted(items, key=lambda item: item.updated_at, reverse=True)

    async def update(
        self,
        insurance_detail: InsuranceDetailModel,
        updates: dict[str, Any],
    ) -> InsuranceDetailModel:
        """Apply partial updates to an insurance-detail document and save it."""

        for field_name, field_value in updates.items():
            setattr(insurance_detail, field_name, field_value)

        insurance_detail.updated_at = datetime.now(timezone.utc)
        await self.engine.save(insurance_detail)
        return insurance_detail

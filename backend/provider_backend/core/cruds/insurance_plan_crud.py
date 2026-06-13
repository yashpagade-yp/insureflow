"""CRUD helpers for insurance-plan documents in the provider backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from odmantic import ObjectId

from ..database.database import get_engine
from ..models.insurance_model import InsuranceModel, InsuranceType


class InsurancePlanCrud:
    """Provides database operations for provider insurance plans."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, plan: InsuranceModel) -> InsuranceModel:
        """Persist a new insurance plan document."""

        await self.engine.save(plan)
        return plan

    async def get_by_id(self, object_id: str | ObjectId) -> InsuranceModel | None:
        """Return one insurance plan by ODMantic object id."""

        return await self.engine.find_one(InsuranceModel, InsuranceModel.id == object_id)

    async def get_by_plan_code(self, plan_code: str) -> InsuranceModel | None:
        """Return one insurance plan by unique provider plan code."""

        return await self.engine.find_one(
            InsuranceModel,
            InsuranceModel.plan_code == plan_code,
        )

    async def list_all(self) -> list[InsuranceModel]:
        """Return all insurance plans, newest first."""

        plans = await self.engine.find(InsuranceModel)
        return sorted(plans, key=lambda item: item.created_at, reverse=True)

    async def list_by_insurance_type(
        self,
        insurance_type: InsuranceType,
    ) -> list[InsuranceModel]:
        """Return all plans matching one insurance type."""

        plans = await self.engine.find(
            InsuranceModel,
            InsuranceModel.insurance_type == insurance_type,
        )
        return sorted(plans, key=lambda item: item.created_at, reverse=True)

    async def update(
        self,
        plan: InsuranceModel,
        updates: dict[str, Any],
    ) -> InsuranceModel:
        """Apply partial updates to an insurance plan and save it."""

        for field_name, field_value in updates.items():
            setattr(plan, field_name, field_value)

        plan.updated_at = datetime.now(timezone.utc)
        await self.engine.save(plan)
        return plan

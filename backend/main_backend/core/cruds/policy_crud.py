"""CRUD helpers for policy documents in the main backend."""

from __future__ import annotations

from datetime import datetime, timezone

from odmantic import ObjectId

from ..database.database import get_engine
from ..models.policy_model import PolicyModel


class PolicyCrud:
    """Provides database operations for issued policy documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, policy: PolicyModel) -> PolicyModel:
        """Persist a new policy document."""

        await self.engine.save(policy)
        return policy

    async def get_by_id(self, object_id: str | ObjectId) -> PolicyModel | None:
        """Return one policy by ODMantic object id."""

        return await self.engine.find_one(PolicyModel, PolicyModel.id == object_id)

    async def get_by_policy_number(self, policy_number: str) -> PolicyModel | None:
        """Return one policy by business policy number."""

        return await self.engine.find_one(
            PolicyModel,
            PolicyModel.policy_number == policy_number,
        )

    async def get_by_transaction_id(self, transaction_id: str) -> PolicyModel | None:
        """Return one policy linked to a transaction."""

        return await self.engine.find_one(
            PolicyModel,
            PolicyModel.transaction_id == transaction_id,
        )

    async def list_by_user_id(self, user_id: str) -> list[PolicyModel]:
        """Return all policies for one user, newest first."""

        policies = await self.engine.find(PolicyModel, PolicyModel.user_id == user_id)
        return sorted(policies, key=lambda item: item.created_at, reverse=True)

    async def update_pdf_url(self, policy: PolicyModel, pdf_url: str) -> PolicyModel:
        """Update the generated PDF URL on a policy."""

        policy.pdf_url = pdf_url
        policy.issued_at = datetime.now(timezone.utc)
        await self.engine.save(policy)
        return policy

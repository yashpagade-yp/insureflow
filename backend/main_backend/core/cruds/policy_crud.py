"""CRUD helpers for policy documents in the main backend."""

from __future__ import annotations

from datetime import datetime, timezone

from odmantic import ObjectId

from ...commons.logger import logger
from ..database.database import get_engine
from ..models.policy_model import PolicyModel

logging = logger(__name__)


class PolicyCrud:
    """Provides database operations for issued policy documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, policy: PolicyModel) -> PolicyModel:
        """Persist a new policy document."""
        try:
            logging.info("Executing PolicyCrud.create function")
            await self.engine.save(policy)
            return policy
        except Exception as error:
            logging.error("Error in PolicyCrud.create function: %s", error)
            raise

    async def get_by_id(self, object_id: str | ObjectId) -> PolicyModel | None:
        """Return one policy by ODMantic object id."""
        try:
            logging.info("Executing PolicyCrud.get_by_id function")
            if isinstance(object_id, str):
                if len(object_id) != 24:
                    return None
                object_id = ObjectId(object_id)
            return await self.engine.find_one(PolicyModel, PolicyModel.id == object_id)
        except Exception as error:
            logging.error("Error in PolicyCrud.get_by_id function: %s", error)
            raise

    async def get_by_policy_number(self, policy_number: str) -> PolicyModel | None:
        """Return one policy by business policy number."""
        try:
            logging.info("Executing PolicyCrud.get_by_policy_number function")
            return await self.engine.find_one(
                PolicyModel,
                PolicyModel.policy_number == policy_number,
            )
        except Exception as error:
            logging.error(
                "Error in PolicyCrud.get_by_policy_number function: %s", error
            )
            raise

    async def get_by_transaction_id(self, transaction_id: str) -> PolicyModel | None:
        """Return one policy linked to a transaction."""
        try:
            logging.info("Executing PolicyCrud.get_by_transaction_id function")
            return await self.engine.find_one(
                PolicyModel,
                PolicyModel.transaction_id == transaction_id,
            )
        except Exception as error:
            logging.error(
                "Error in PolicyCrud.get_by_transaction_id function: %s", error
            )
            raise

    async def list_by_user_id(self, user_id: str) -> list[PolicyModel]:
        """Return all policies for one user, newest first."""
        try:
            logging.info("Executing PolicyCrud.list_by_user_id function")
            policies = await self.engine.find(PolicyModel, PolicyModel.user_id == user_id)
            return sorted(policies, key=lambda item: item.created_at, reverse=True)
        except Exception as error:
            logging.error("Error in PolicyCrud.list_by_user_id function: %s", error)
            raise

    async def update_pdf_url(self, policy: PolicyModel, pdf_url: str) -> PolicyModel:
        """Update the generated PDF URL on a policy."""
        try:
            logging.info("Executing PolicyCrud.update_pdf_url function")
            policy.pdf_url = pdf_url
            policy.issued_at = datetime.now(timezone.utc)
            await self.engine.save(policy)
            return policy
        except Exception as error:
            logging.error("Error in PolicyCrud.update_pdf_url function: %s", error)
            raise

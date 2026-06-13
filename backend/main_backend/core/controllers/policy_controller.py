"""Controller logic for issued-policy flows in the main backend."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import HTTPException, status

from ...commons.logger import logger
from ..apis.schemas.response_schema.policy_response_schema import (
    PolicyAddOnResponse,
    PolicyListResponse,
    PolicyPdfResponse,
    PolicyResponse,
)
from ..cruds.policy_crud import PolicyCrud
from ..cruds.transaction_crud import TransactionCrud
from ..models.policy_model import PolicyAddOn, PolicyModel
from ..models.transaction_model import TransactionStatus

logging = logger(__name__)


class PolicyController:
    """Handles policy issuance and policy retrieval business logic."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependencies."""

        self.policy_crud = PolicyCrud()
        self.transaction_crud = TransactionCrud()

    async def issue_policy(
        self,
        transaction_id: str,
        user_id: str,
        company_name: str,
        plan_name: str,
        coverage_amount: float,
        base_premium: float,
        add_ons: list[dict[str, Any]],
        add_on_total: float,
        tax_amount: float,
        total_premium: float,
        payment_reference: str,
        pdf_url: str | None = None,
        duration_years: int = 1,
    ) -> PolicyResponse:
        """Create a policy after successful payment and mark the transaction complete."""
        try:
            logging.info("Executing PolicyController.issue_policy function")
            existing_policy = await self.policy_crud.get_by_transaction_id(transaction_id)
            if existing_policy is not None:
                logging.warning(
                    "Policy already exists for transaction %s", transaction_id
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A policy already exists for this transaction.",
                )

            start_date = date.today()
            end_date = start_date + timedelta(days=365 * max(duration_years, 1))
            policy_add_ons = [PolicyAddOn.model_validate(item) for item in add_ons]
            policy = await self.policy_crud.create(
                PolicyModel.model_validate(
                    {
                        "transaction_id": transaction_id,
                        "user_id": user_id,
                        "company_name": company_name,
                        "plan_name": plan_name,
                        "coverage_amount": coverage_amount,
                        "base_premium": base_premium,
                        "add_ons": policy_add_ons,
                        "add_on_total": add_on_total,
                        "tax_amount": tax_amount,
                        "total_premium": total_premium,
                        "start_date": start_date,
                        "end_date": end_date,
                        "payment_reference": payment_reference,
                        "pdf_url": pdf_url,
                    }
                )
            )

            transaction = await self.transaction_crud.get_by_transaction_id(transaction_id)
            if transaction is not None:
                await self.transaction_crud.update_status(
                    transaction,
                    TransactionStatus.PURCHASED,
                )

            logging.info("Policy issued successfully for transaction %s", transaction_id)
            return self._build_policy_response(policy)
        except HTTPException as httperror:
            logging.error(
                "Error in PolicyController.issue_policy function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in PolicyController.issue_policy function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to issue policy.",
            )

    async def attach_policy_pdf(
        self,
        policy_number: str,
        pdf_url: str,
    ) -> PolicyPdfResponse:
        """Attach a generated PDF URL to an issued policy."""
        try:
            logging.info("Executing PolicyController.attach_policy_pdf function")
            policy = await self.policy_crud.get_by_policy_number(policy_number)
            if policy is None:
                logging.warning("Policy not found for policy number %s", policy_number)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Policy not found.",
                )

            policy = await self.policy_crud.update_pdf_url(policy, pdf_url)
            return PolicyPdfResponse(
                policy_number=policy.policy_number,
                pdf_url=policy.pdf_url,
                policy_status=policy.policy_status.value,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in PolicyController.attach_policy_pdf function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in PolicyController.attach_policy_pdf function: %s", error
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to attach policy PDF.",
            )

    async def get_policy(self, policy_number: str) -> PolicyResponse:
        """Return one issued policy by business policy number."""
        try:
            logging.info("Executing PolicyController.get_policy function")
            policy = await self.policy_crud.get_by_policy_number(policy_number)
            if policy is None:
                logging.warning("Policy not found for policy number %s", policy_number)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Policy not found.",
                )
            return self._build_policy_response(policy)
        except HTTPException as httperror:
            logging.error(
                "Error in PolicyController.get_policy function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in PolicyController.get_policy function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch policy.",
            )

    async def list_user_policies(self, user_id: str) -> PolicyListResponse:
        """Return all policies for one user."""
        try:
            logging.info("Executing PolicyController.list_user_policies function")
            policies = await self.policy_crud.list_by_user_id(user_id)
            return PolicyListResponse(
                items=[self._build_policy_response(item) for item in policies],
                total_count=len(policies),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in PolicyController.list_user_policies function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in PolicyController.list_user_policies function: %s", error
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list user policies.",
            )

    def _build_policy_response(self, policy: PolicyModel) -> PolicyResponse:
        """Convert a policy document into the public response schema."""

        return PolicyResponse(
            policy_number=policy.policy_number,
            transaction_id=policy.transaction_id,
            user_id=policy.user_id,
            company_name=policy.company_name,
            plan_name=policy.plan_name,
            coverage_amount=policy.coverage_amount,
            base_premium=policy.base_premium,
            add_ons=[
                PolicyAddOnResponse(name=item.name, price=item.price)
                for item in policy.add_ons
            ],
            add_on_total=policy.add_on_total,
            tax_amount=policy.tax_amount,
            total_premium=policy.total_premium,
            start_date=policy.start_date,
            end_date=policy.end_date,
            payment_reference=policy.payment_reference,
            pdf_url=policy.pdf_url,
            policy_status=policy.policy_status.value,
            issued_at=policy.issued_at,
            created_at=policy.created_at,
        )

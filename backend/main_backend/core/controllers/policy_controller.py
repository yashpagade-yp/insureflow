"""Controller logic for issued-policy flows in the main backend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status

from commons.logger import logger
from core.apis.schemas.response_schema.policy_response_schema import (
    PolicyAddOnResponse,
    PolicyListResponse,
    PolicyPdfResponse,
    PolicyResponse,
)
from core.cruds.policy_crud import PolicyCrud
from core.cruds.transaction_crud import TransactionCrud
from core.models.policy_model import PolicyAddOn, PolicyModel, generate_policy_number
from core.models.transaction_model import TransactionStatus
from core.services.policy_document_service import PolicyDocumentService

logging = logger(__name__)


class PolicyController:
    """Handles policy issuance and policy retrieval business logic."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependencies."""

        self.policy_crud = PolicyCrud()
        self.transaction_crud = TransactionCrud()
        self.policy_document_service = PolicyDocumentService()

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
        """Create a policy after successful payment and mark the transaction complete.

        Args:
            transaction_id: Transaction identifier linked to the purchase.
            user_id: User identifier who owns the issued policy.
            company_name: Issuing insurance company name.
            plan_name: Selected insurance plan name.
            coverage_amount: Coverage amount stored on the issued policy.
            base_premium: Base premium before add-ons and tax.
            add_ons: Selected add-ons to snapshot onto the policy.
            add_on_total: Total price contributed by selected add-ons.
            tax_amount: Tax amount applied to the premium.
            total_premium: Final total premium paid.
            payment_reference: Linked payment reference.
            pdf_url: Optional generated PDF URL to store immediately.
            duration_years: Policy term duration in years.

        Returns:
            PolicyResponse: Serialized issued policy response.

        Raises:
            HTTPException: If required identifiers are invalid, a policy already
                exists, or policy issuance fails.
        """
        try:
            logging.info("Executing PolicyController.issue_policy function")
            normalized_transaction_id = transaction_id.strip()
            normalized_user_id = user_id.strip()
            normalized_company_name = company_name.strip()
            normalized_plan_name = plan_name.strip()
            normalized_payment_reference = payment_reference.strip()
            if (
                not normalized_transaction_id
                or not normalized_user_id
                or not normalized_company_name
                or not normalized_plan_name
                or not normalized_payment_reference
            ):
                logging.warning("Policy issuance received empty required values")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction, user, company, plan, and payment reference are required.",
                )

            existing_policy = await self.policy_crud.get_by_transaction_id(
                normalized_transaction_id
            )
            if existing_policy is not None:
                logging.warning(
                    "Policy already exists for transaction %s",
                    normalized_transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A policy already exists for this transaction.",
                )

            start_date = datetime.now(timezone.utc).replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            end_date = start_date + timedelta(days=365 * max(duration_years, 1))
            policy_add_ons = [PolicyAddOn.model_validate(item) for item in add_ons]
            policy_number = generate_policy_number()
            generated_pdf_url = pdf_url or self.policy_document_service.generate_policy_pdf(
                policy_number=policy_number,
                user_id=normalized_user_id,
                company_name=normalized_company_name,
                plan_name=normalized_plan_name,
                payment_reference=normalized_payment_reference,
                total_premium=total_premium,
                start_date=start_date.date().isoformat(),
                end_date=end_date.date().isoformat(),
            )
            policy = await self.policy_crud.create(
                PolicyModel.model_validate(
                    {
                        "policy_number": policy_number,
                        "transaction_id": normalized_transaction_id,
                        "user_id": normalized_user_id,
                        "company_name": normalized_company_name,
                        "plan_name": normalized_plan_name,
                        "coverage_amount": coverage_amount,
                        "base_premium": base_premium,
                        "add_ons": policy_add_ons,
                        "add_on_total": add_on_total,
                        "tax_amount": tax_amount,
                        "total_premium": total_premium,
                        "start_date": start_date,
                        "end_date": end_date,
                        "payment_reference": normalized_payment_reference,
                        "pdf_url": generated_pdf_url,
                    }
                )
            )

            transaction = await self.transaction_crud.get_by_transaction_id(
                normalized_transaction_id
            )
            if transaction is not None:
                await self.transaction_crud.update_status(
                    transaction,
                    TransactionStatus.PURCHASED,
                )

            logging.info(
                "Policy issued successfully for transaction %s",
                normalized_transaction_id,
            )
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
        """Attach a generated PDF URL to an issued policy.

        Args:
            policy_number: Business-facing policy number to update.
            pdf_url: Generated policy PDF URL to store.

        Returns:
            PolicyPdfResponse: Updated policy PDF metadata response.

        Raises:
            HTTPException: If the policy number or PDF URL is invalid, or the
                policy cannot be updated.
        """
        try:
            logging.info("Executing PolicyController.attach_policy_pdf function")
            normalized_policy_number = policy_number.strip()
            normalized_pdf_url = pdf_url.strip()
            if not normalized_policy_number or not normalized_pdf_url:
                logging.warning("Policy PDF attachment received empty values")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Policy number and PDF URL are required.",
                )

            policy = await self.policy_crud.get_by_policy_number(normalized_policy_number)
            if policy is None:
                logging.warning(
                    "Policy not found for policy number %s",
                    normalized_policy_number,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Policy not found.",
                )

            policy = await self.policy_crud.update_pdf_url(policy, normalized_pdf_url)
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
        """Return one issued policy by business policy number.

        Args:
            policy_number: Business-facing policy number to fetch.

        Returns:
            PolicyResponse: Serialized issued policy response.

        Raises:
            HTTPException: If the policy number is invalid or the policy cannot
                be found.
        """
        try:
            logging.info("Executing PolicyController.get_policy function")
            normalized_policy_number = policy_number.strip()
            if not normalized_policy_number:
                logging.warning("Empty policy_number provided for lookup")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Policy number is required.",
                )

            policy = await self.policy_crud.get_by_policy_number(normalized_policy_number)
            if policy is None:
                logging.warning(
                    "Policy not found for policy number %s",
                    normalized_policy_number,
                )
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
        """Return all policies for one user.

        Args:
            user_id: User identifier whose policies should be listed.

        Returns:
            PolicyListResponse: Ordered list of issued policies for the user.

        Raises:
            HTTPException: If the user identifier is invalid or the policies
                cannot be listed.
        """
        try:
            logging.info("Executing PolicyController.list_user_policies function")
            normalized_user_id = user_id.strip()
            if not normalized_user_id:
                logging.warning("Empty user_id provided for policy listing")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User id is required.",
                )

            policies = await self.policy_crud.list_by_user_id(normalized_user_id)
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

    async def list_all_policies(self) -> PolicyListResponse:
        """Return all issued policies for the admin dashboard.

        Returns:
            PolicyListResponse: Ordered list of all issued policies.

        Raises:
            HTTPException: If policy listing fails.
        """

        try:
            logging.info("Executing PolicyController.list_all_policies function")
            policies = await self.policy_crud.list_all()
            return PolicyListResponse(
                items=[self._build_policy_response(item) for item in policies],
                total_count=len(policies),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in PolicyController.list_all_policies function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in PolicyController.list_all_policies function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list policies.",
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
            start_date=policy.start_date.date(),
            end_date=policy.end_date.date(),
            payment_reference=policy.payment_reference,
            pdf_url=policy.pdf_url,
            policy_status=policy.policy_status.value,
            issued_at=policy.issued_at,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        )

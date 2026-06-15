"""Controller logic for payment integration flows in the main backend."""

from __future__ import annotations

from fastapi import HTTPException, status

from commons.logger import logger
from core.apis.schemas.request_schema.payment_request_schema import (
    PaymentCreateRequest,
    PaymentOtpVerifyRequest,
)
from core.apis.schemas.response_schema.payment_response_schema import (
    PaymentCreateResponse,
    PaymentOtpSendResponse,
    PaymentOtpVerifyResponse,
    PaymentStatusResponse,
)
from core.cruds.transaction_crud import TransactionCrud
from core.models.transaction_model import TransactionStatus
from core.services.provider_service import ProviderService
from core.controllers.policy_controller import PolicyController

logging = logger(__name__)


class PaymentController:
    """Handles provider-backed payment orchestration in the main backend."""

    def __init__(self) -> None:
        """Initialise the controller with its service and CRUD dependencies."""

        self.provider_service = ProviderService()
        self.transaction_crud = TransactionCrud()
        self.policy_controller = PolicyController()

    async def create_payment(self, payload: PaymentCreateRequest) -> PaymentCreateResponse:
        """Create a provider-side payment record and mark the transaction pending."""

        try:
            logging.info("Executing PaymentController.create_payment function")
            provider_response = await self.provider_service.create_payment(
                transaction_id=payload.transaction_id,
                user_id=payload.user_id,
                amount=payload.amount,
            )
            transaction = await self.transaction_crud.get_by_transaction_id(
                payload.transaction_id
            )
            if transaction is not None:
                await self.transaction_crud.update_status(
                    transaction,
                    TransactionStatus.PAYMENT_PENDING,
                )

            return PaymentCreateResponse(
                message=provider_response["message"],
                transaction_id=provider_response["transaction_id"],
                payment_reference=provider_response["payment_reference"],
                payment_status=provider_response["payment_status"],
                amount=provider_response["amount"],
                gateway_url=provider_response.get("gateway_url"),
                created_at=provider_response["created_at"],
            )
        except HTTPException as httperror:
            logging.error(
                "Error in PaymentController.create_payment function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error("Error in PaymentController.create_payment function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment.",
            )

    async def send_payment_otp(self, payment_reference: str) -> PaymentOtpSendResponse:
        """Trigger provider-side payment OTP generation."""

        try:
            logging.info("Executing PaymentController.send_payment_otp function")
            provider_response = await self.provider_service.send_payment_otp(
                payment_reference
            )
            return PaymentOtpSendResponse(
                message=provider_response["message"],
                payment_reference=provider_response["payment_reference"],
                otp_expires_at=provider_response["otp_expires_at"],
                plain_otp=provider_response.get("plain_otp"),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in PaymentController.send_payment_otp function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error("Error in PaymentController.send_payment_otp function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send payment OTP.",
            )

    async def verify_payment_otp(
        self,
        payload: PaymentOtpVerifyRequest,
    ) -> PaymentOtpVerifyResponse:
        """Verify provider-side payment OTP and issue a local policy on success."""

        try:
            logging.info("Executing PaymentController.verify_payment_otp function")
            transaction = await self.transaction_crud.get_by_transaction_id(
                payload.transaction_id
            )
            if transaction is None:
                logging.warning(
                    "Transaction %s not found during payment OTP verification",
                    payload.transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )

            provider_response = await self.provider_service.verify_payment_otp(
                transaction_id=payload.transaction_id,
                payment_reference=payload.payment_reference,
                otp=payload.otp,
            )
            quote_response = await self.provider_service.get_quotes(payload.transaction_id)
            selected_plan_id = quote_response.get("selected_plan_id")
            if not selected_plan_id:
                logging.warning(
                    "Selected plan missing for transaction %s during policy issuance",
                    payload.transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected plan not found for policy issuance.",
                )

            selected_item = next(
                (
                    item
                    for item in quote_response.get("items", [])
                    if item.get("plan_id") == selected_plan_id
                ),
                None,
            )
            if selected_item is None:
                logging.warning(
                    "Selected quote item %s missing for transaction %s",
                    selected_plan_id,
                    payload.transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected quote item not found for policy issuance.",
                )

            policy_response = await self.policy_controller.issue_policy(
                transaction_id=payload.transaction_id,
                user_id=transaction.user_id,
                company_name=selected_item["company_name"],
                plan_name=selected_item["plan_name"],
                coverage_amount=selected_item["coverage_amount"],
                base_premium=selected_item["base_premium"],
                add_ons=selected_item.get("selected_add_ons", []),
                add_on_total=selected_item["add_on_total"],
                tax_amount=selected_item["tax_amount"],
                total_premium=selected_item["total_premium"],
                payment_reference=provider_response["payment_reference"],
                duration_years=selected_item["duration_years"],
            )

            return PaymentOtpVerifyResponse(
                message=provider_response["message"],
                transaction_id=provider_response["transaction_id"],
                payment_reference=provider_response["payment_reference"],
                payment_status=provider_response["payment_status"],
                verified_at=provider_response["verified_at"],
                policy_number=policy_response.policy_number,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in PaymentController.verify_payment_otp function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in PaymentController.verify_payment_otp function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify payment OTP.",
            )

    async def get_payment_status(self, payment_reference: str) -> PaymentStatusResponse:
        """Fetch provider-side payment status details."""

        try:
            logging.info("Executing PaymentController.get_payment_status function")
            provider_response = await self.provider_service.get_payment_status(
                payment_reference
            )
            return PaymentStatusResponse(
                transaction_id=provider_response["transaction_id"],
                payment_reference=provider_response["payment_reference"],
                payment_status=provider_response["payment_status"],
                amount=provider_response["amount"],
                gateway_url=provider_response.get("gateway_url"),
                updated_at=provider_response["updated_at"],
            )
        except HTTPException as httperror:
            logging.error(
                "Error in PaymentController.get_payment_status function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error("Error in PaymentController.get_payment_status function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch payment status.",
            )

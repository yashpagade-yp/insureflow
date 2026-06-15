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
        """Create a provider-side payment record and mark the transaction pending.

        Args:
            payload: Transaction id, user id, and amount for the payment flow.

        Returns:
            PaymentCreateResponse: Payment record created by the provider
                backend and mapped into the main-backend schema.

        Raises:
            HTTPException: If identifiers are invalid, the transaction does not
                exist, or the provider payment cannot be created.
        """

        try:
            logging.info("Executing PaymentController.create_payment function")
            normalized_transaction_id = payload.transaction_id.strip()
            normalized_user_id = payload.user_id.strip()
            if not normalized_transaction_id or not normalized_user_id:
                logging.warning("Payment creation received empty identifiers")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction id and user id are required.",
                )

            transaction = await self.transaction_crud.get_by_transaction_id(
                normalized_transaction_id
            )
            if transaction is None:
                logging.warning(
                    "Transaction %s not found during payment creation",
                    normalized_transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )

            provider_response = await self.provider_service.create_payment(
                transaction_id=normalized_transaction_id,
                user_id=normalized_user_id,
                amount=payload.amount,
            )
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
        """Trigger provider-side payment OTP generation.

        Args:
            payment_reference: Business payment reference for the payment flow.

        Returns:
            PaymentOtpSendResponse: Provider payment-OTP generation response.

        Raises:
            HTTPException: If the payment reference is invalid or OTP generation
                fails.
        """

        try:
            logging.info("Executing PaymentController.send_payment_otp function")
            normalized_payment_reference = payment_reference.strip()
            if not normalized_payment_reference:
                logging.warning("Empty payment_reference provided for OTP send")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment reference is required.",
                )
            provider_response = await self.provider_service.send_payment_otp(
                normalized_payment_reference
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
        """Verify provider-side payment OTP and issue a local policy on success.

        Args:
            payload: Transaction id, payment reference, and OTP for payment
                verification.

        Returns:
            PaymentOtpVerifyResponse: Verified payment response including the
                issued local policy number.

        Raises:
            HTTPException: If verification input is invalid, payment verification
                fails, or policy issuance cannot be completed.
        """

        try:
            logging.info("Executing PaymentController.verify_payment_otp function")
            normalized_transaction_id = payload.transaction_id.strip()
            normalized_payment_reference = payload.payment_reference.strip()
            normalized_otp = payload.otp.strip()
            if (
                not normalized_transaction_id
                or not normalized_payment_reference
                or not normalized_otp
            ):
                logging.warning("Payment OTP verification received empty values")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction id, payment reference, and OTP are required.",
                )

            transaction = await self.transaction_crud.get_by_transaction_id(
                normalized_transaction_id
            )
            if transaction is None:
                logging.warning(
                    "Transaction %s not found during payment OTP verification",
                    normalized_transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found.",
                )

            provider_response = await self.provider_service.verify_payment_otp(
                transaction_id=normalized_transaction_id,
                payment_reference=normalized_payment_reference,
                otp=normalized_otp,
            )
            quote_response = await self.provider_service.get_quotes(
                normalized_transaction_id
            )
            selected_plan_id = quote_response.get("selected_plan_id")
            if not selected_plan_id:
                logging.warning(
                    "Selected plan missing for transaction %s during policy issuance",
                    normalized_transaction_id,
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
                    normalized_transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected quote item not found for policy issuance.",
                )

            policy_response = await self.policy_controller.issue_policy(
                transaction_id=normalized_transaction_id,
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
        """Fetch provider-side payment status details.

        Args:
            payment_reference: Business payment reference to inspect.

        Returns:
            PaymentStatusResponse: Current provider payment status details.

        Raises:
            HTTPException: If the payment reference is invalid or the provider
                payment status cannot be fetched.
        """

        try:
            logging.info("Executing PaymentController.get_payment_status function")
            normalized_payment_reference = payment_reference.strip()
            if not normalized_payment_reference:
                logging.warning("Empty payment_reference provided for status lookup")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment reference is required.",
                )
            provider_response = await self.provider_service.get_payment_status(
                normalized_payment_reference
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

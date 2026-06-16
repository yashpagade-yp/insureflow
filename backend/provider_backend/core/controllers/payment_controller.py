"""Controller logic for mock payment flows in the provider backend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from commons.auth import generate_otp, hash_otp, log_otp_for_dev, verify_hashed_otp
from commons.logger import logger
from core.apis.schemas.response_schema.payment_response_schema import (
    PaymentCreateResponse,
    PaymentListResponse,
    PaymentOtpSendResponse,
    PaymentOtpVerifyResponse,
    PaymentStatusResponse,
)
from core.cruds.payment_crud import PaymentCrud
from core.models.payment_model import PaymentModel, PaymentOtp

logging = logger(__name__)

OTP_EXPIRY_MINUTES = 10
OTP_REQUEST_INTERVAL_SECONDS = 30
MAX_OTP_ATTEMPTS = 5
OTP_ATTEMPT_WINDOW_SECONDS = 3600


class PaymentController:
    """Handles mock payment creation and payment OTP verification."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependency."""

        self.payment_crud = PaymentCrud()

    async def create_payment(
        self,
        transaction_id: str,
        user_id: str,
        amount: float,
    ) -> PaymentCreateResponse:
        """Create a provider payment record for one transaction.

        Args:
            transaction_id: Related transaction identifier from the main backend.
            user_id: User identifier linked to the transaction.
            amount: Final amount to record for the payment.

        Returns:
            PaymentCreateResponse: Created provider payment response.

        Raises:
            HTTPException: If identifiers are invalid or the payment cannot be
                created.
        """
        try:
            logging.info("Executing PaymentController.create_payment function")
            normalized_transaction_id = transaction_id.strip()
            normalized_user_id = user_id.strip()
            if not normalized_transaction_id or not normalized_user_id:
                logging.warning("Provider payment creation received empty identifiers")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction id and user id are required.",
                )

            existing_payment = await self.payment_crud.get_by_transaction_id(
                normalized_transaction_id
            )
            if existing_payment is not None:
                logging.warning(
                    "Payment already exists for transaction %s",
                    normalized_transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A payment already exists for this transaction.",
                )

            payment = PaymentModel.model_validate(
                {
                    "transaction_id": normalized_transaction_id,
                    "user_id": normalized_user_id,
                    "amount": amount,
                }
            )
            payment.gateway_url = f"/mock-gateway/payments/{payment.payment_reference}"
            payment = await self.payment_crud.create(payment)
            logging.info(
                "Payment record created successfully for transaction %s",
                normalized_transaction_id,
            )
            return PaymentCreateResponse(
                message="Payment record created successfully.",
                transaction_id=payment.transaction_id,
                payment_reference=payment.payment_reference,
                payment_status=payment.payment_status.value,
                amount=payment.amount,
                gateway_url=payment.gateway_url,
                created_at=payment.created_at,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in PaymentController.create_payment function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in PaymentController.create_payment function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment.",
            )

    async def send_payment_otp(self, payment_reference: str) -> PaymentOtpSendResponse:
        """Generate and store a new mock payment OTP.

        Args:
            payment_reference: Business payment reference for the current
                payment.

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
                logging.warning("Empty payment_reference provided for provider OTP send")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment reference is required.",
                )

            payment = await self.payment_crud.get_by_payment_reference(
                normalized_payment_reference
            )
            if payment is None:
                logging.warning(
                    "Payment not found for payment reference %s",
                    normalized_payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found.",
                )

            now = datetime.now(timezone.utc)
            if payment.payment_otp is not None:
                payment.payment_otp = self._reset_payment_attempt_window_if_needed(
                    payment.payment_otp,
                    now,
                )
            if (
                payment.payment_otp is not None
                and (now - payment.payment_otp.requested_at).total_seconds()
                < OTP_REQUEST_INTERVAL_SECONDS
            ):
                logging.warning(
                    "Payment OTP requested too frequently for payment reference %s",
                    normalized_payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Please wait before requesting a new payment OTP.",
                )

            plain_otp = generate_otp()
            log_otp_for_dev(
                flow_name="payment_verification",
                recipient=payment_reference,
                otp=plain_otp,
            )
            payment_otp = PaymentOtp(
                code_hash=hash_otp(plain_otp),
                expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES),
                requested_at=now,
                attempt_count=0,
                attempt_window_started_at=now,
                verified_at=None,
            )
            await self.payment_crud.save_payment_otp(payment, payment_otp)
            logging.info(
                "Payment OTP generated successfully for payment reference %s",
                normalized_payment_reference,
            )
            return PaymentOtpSendResponse(
                message="Payment OTP generated successfully.",
                payment_reference=payment.payment_reference,
                otp_expires_at=payment_otp.expires_at,
                plain_otp=plain_otp,
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
        transaction_id: str,
        payment_reference: str,
        otp: str,
    ) -> PaymentOtpVerifyResponse:
        """Verify a stored payment OTP and mark the payment successful.

        Args:
            transaction_id: Related transaction identifier from the main backend.
            payment_reference: Business payment reference for the current payment.
            otp: Customer OTP provided for payment verification.

        Returns:
            PaymentOtpVerifyResponse: Verified payment response.

        Raises:
            HTTPException: If identifiers are invalid or the OTP verification
                flow cannot be completed.
        """
        try:
            logging.info("Executing PaymentController.verify_payment_otp function")
            normalized_transaction_id = transaction_id.strip()
            normalized_payment_reference = payment_reference.strip()
            normalized_otp = otp.strip()
            if (
                not normalized_transaction_id
                or not normalized_payment_reference
                or not normalized_otp
            ):
                logging.warning(
                    "Provider payment OTP verification received empty values"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction id, payment reference, and OTP are required.",
                )

            payment = await self.payment_crud.get_by_payment_reference(
                normalized_payment_reference
            )
            if payment is None or payment.transaction_id != normalized_transaction_id:
                logging.warning(
                    "Payment not found for transaction %s and payment reference %s",
                    normalized_transaction_id,
                    normalized_payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found for this transaction.",
                )
            if payment.payment_otp is None:
                logging.warning(
                    "Payment OTP not generated yet for payment reference %s",
                    normalized_payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment OTP has not been generated yet.",
                )

            now = datetime.now(timezone.utc)
            payment.payment_otp = self._reset_payment_attempt_window_if_needed(
                payment.payment_otp,
                now,
            )
            if payment.payment_otp.expires_at < now:
                logging.warning(
                    "Expired payment OTP used for payment reference %s",
                    normalized_payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment OTP has expired. Please request a new OTP.",
                )

            if payment.payment_otp.attempt_count >= MAX_OTP_ATTEMPTS:
                logging.warning(
                    "Maximum payment OTP attempts exceeded for payment reference %s",
                    normalized_payment_reference,
                )
                payment = await self.payment_crud.mark_failed(payment)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Maximum payment OTP verification attempts exceeded. Please request a new payment session.",
                )

            if not verify_hashed_otp(normalized_otp, payment.payment_otp.code_hash):
                payment.payment_otp.attempt_count += 1
                await self.payment_crud.save_payment_otp(payment, payment.payment_otp)
                logging.warning(
                    "Invalid payment OTP submitted for payment reference %s",
                    normalized_payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid payment OTP.",
                )

            payment.payment_otp.verified_at = now
            await self.payment_crud.save_payment_otp(payment, payment.payment_otp)
            payment = await self.payment_crud.mark_success(payment)
            verified_at = payment.payment_otp.verified_at
            if verified_at is None:
                logging.error(
                    "Payment OTP verification timestamp missing for payment reference %s",
                    normalized_payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Payment OTP verification timestamp is missing.",
                )
            logging.info(
                "Payment OTP verified successfully for payment reference %s",
                normalized_payment_reference,
            )
            return PaymentOtpVerifyResponse(
                message="Payment OTP verified successfully.",
                transaction_id=payment.transaction_id,
                payment_reference=payment.payment_reference,
                payment_status=payment.payment_status.value,
                verified_at=verified_at,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in PaymentController.verify_payment_otp function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in PaymentController.verify_payment_otp function: %s", error
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify payment OTP.",
            )

    async def get_payment_status(self, payment_reference: str) -> PaymentStatusResponse:
        """Return payment status details for one payment reference.

        Args:
            payment_reference: Business payment reference to inspect.

        Returns:
            PaymentStatusResponse: Current provider payment status details.

        Raises:
            HTTPException: If the payment reference is invalid or the payment
                cannot be found.
        """
        try:
            logging.info("Executing PaymentController.get_payment_status function")
            normalized_payment_reference = payment_reference.strip()
            if not normalized_payment_reference:
                logging.warning(
                    "Empty payment_reference provided for provider payment status lookup"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment reference is required.",
                )

            payment = await self.payment_crud.get_by_payment_reference(
                normalized_payment_reference
            )
            if payment is None:
                logging.warning(
                    "Payment not found for payment reference %s",
                    normalized_payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found.",
                )

            return PaymentStatusResponse(
                transaction_id=payment.transaction_id,
                payment_reference=payment.payment_reference,
                payment_status=payment.payment_status.value,
                amount=payment.amount,
                gateway_url=payment.gateway_url,
                updated_at=payment.updated_at,
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

    async def list_payments(self) -> PaymentListResponse:
        """Return all provider payment records for the admin dashboard."""

        try:
            logging.info("Executing PaymentController.list_payments function")
            payments = await self.payment_crud.list_all()
            return PaymentListResponse(
                items=[self._build_payment_status_response(item) for item in payments],
                total_count=len(payments),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in PaymentController.list_payments function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error("Error in PaymentController.list_payments function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list payments.",
            )

    def _reset_payment_attempt_window_if_needed(
        self,
        payment_otp: PaymentOtp,
        now: datetime,
    ) -> PaymentOtp:
        """Reset payment OTP attempts when the active attempt window has expired."""

        payment_otp.requested_at = self._ensure_utc_datetime(payment_otp.requested_at)
        payment_otp.expires_at = self._ensure_utc_datetime(payment_otp.expires_at)
        payment_otp.attempt_window_started_at = self._ensure_utc_datetime(
            payment_otp.attempt_window_started_at
        )
        if payment_otp.verified_at is not None:
            payment_otp.verified_at = self._ensure_utc_datetime(payment_otp.verified_at)
        if (
            now - payment_otp.attempt_window_started_at
        ).total_seconds() >= OTP_ATTEMPT_WINDOW_SECONDS:
            payment_otp.attempt_count = 0
            payment_otp.attempt_window_started_at = now
        return payment_otp

    def _ensure_utc_datetime(self, value: datetime) -> datetime:
        """Normalize stored datetimes so comparisons always use UTC-aware values."""

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _build_payment_status_response(self, payment: PaymentModel) -> PaymentStatusResponse:
        """Convert a payment document into the public payment-status schema."""

        return PaymentStatusResponse(
            transaction_id=payment.transaction_id,
            payment_reference=payment.payment_reference,
            payment_status=payment.payment_status.value,
            amount=payment.amount,
            gateway_url=payment.gateway_url,
            updated_at=payment.updated_at,
        )

"""Controller logic for mock payment flows in the provider backend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from ...commons.auth import generate_otp, hash_otp, verify_hashed_otp
from ...commons.logger import logger
from ..apis.schemas.response_schema.payment_response_schema import (
    PaymentCreateResponse,
    PaymentOtpSendResponse,
    PaymentOtpVerifyResponse,
    PaymentStatusResponse,
)
from ..cruds.payment_crud import PaymentCrud
from ..models.payment_model import PaymentModel, PaymentOtp

logging = logger(__name__)


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
        """Create a provider payment record for one transaction."""
        try:
            logging.info("Executing PaymentController.create_payment")
            existing_payment = await self.payment_crud.get_by_transaction_id(
                transaction_id
            )
            if existing_payment is not None:
                logging.warning(
                    "Payment already exists for transaction %s", transaction_id
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A payment already exists for this transaction.",
                )

            payment = PaymentModel(
                transaction_id=transaction_id,
                user_id=user_id,
                amount=amount,
            )
            payment.gateway_url = f"/mock-gateway/payments/{payment.payment_reference}"
            payment = await self.payment_crud.create(payment)
            logging.info(
                "Payment record created successfully for transaction %s",
                transaction_id,
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
        except HTTPException:
            raise
        except Exception as error:
            logging.error("Error in PaymentController.create_payment: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment.",
            )

    async def send_payment_otp(self, payment_reference: str) -> PaymentOtpSendResponse:
        """Generate and store a new mock payment OTP."""
        try:
            logging.info("Executing PaymentController.send_payment_otp")
            payment = await self.payment_crud.get_by_payment_reference(payment_reference)
            if payment is None:
                logging.warning(
                    "Payment not found for payment reference %s", payment_reference
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found.",
                )

            plain_otp = generate_otp()
            now = datetime.now(timezone.utc)
            payment_otp = PaymentOtp(
                code_hash=hash_otp(plain_otp),
                expires_at=now + timedelta(minutes=10),
                requested_at=now,
                attempt_count=0,
                verified_at=None,
            )
            await self.payment_crud.save_payment_otp(payment, payment_otp)
            logging.info(
                "Payment OTP generated successfully for payment reference %s",
                payment_reference,
            )
            return PaymentOtpSendResponse(
                message="Payment OTP generated successfully.",
                payment_reference=payment.payment_reference,
                otp_expires_at=payment_otp.expires_at,
            )
        except HTTPException:
            raise
        except Exception as error:
            logging.error("Error in PaymentController.send_payment_otp: %s", error)
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
        """Verify a stored payment OTP and mark the payment successful."""
        try:
            logging.info("Executing PaymentController.verify_payment_otp")
            payment = await self.payment_crud.get_by_payment_reference(payment_reference)
            if payment is None or payment.transaction_id != transaction_id:
                logging.warning(
                    "Payment not found for transaction %s and payment reference %s",
                    transaction_id,
                    payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found for this transaction.",
                )
            if payment.payment_otp is None:
                logging.warning(
                    "Payment OTP not generated yet for payment reference %s",
                    payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment OTP has not been generated yet.",
                )

            now = datetime.now(timezone.utc)
            if payment.payment_otp.expires_at < now:
                logging.warning(
                    "Expired payment OTP used for payment reference %s",
                    payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment OTP has expired. Please request a new OTP.",
                )

            if not verify_hashed_otp(otp, payment.payment_otp.code_hash):
                payment.payment_otp.attempt_count += 1
                await self.payment_crud.save_payment_otp(payment, payment.payment_otp)
                logging.warning(
                    "Invalid payment OTP submitted for payment reference %s",
                    payment_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid payment OTP.",
                )

            payment.payment_otp.verified_at = now
            await self.payment_crud.save_payment_otp(payment, payment.payment_otp)
            payment = await self.payment_crud.mark_success(payment)
            logging.info(
                "Payment OTP verified successfully for payment reference %s",
                payment_reference,
            )
            return PaymentOtpVerifyResponse(
                message="Payment OTP verified successfully.",
                transaction_id=payment.transaction_id,
                payment_reference=payment.payment_reference,
                payment_status=payment.payment_status.value,
                verified_at=payment.payment_otp.verified_at,
            )
        except HTTPException:
            raise
        except Exception as error:
            logging.error("Error in PaymentController.verify_payment_otp: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify payment OTP.",
            )

    async def get_payment_status(self, payment_reference: str) -> PaymentStatusResponse:
        """Return payment status details for one payment reference."""
        try:
            logging.info("Executing PaymentController.get_payment_status")
            payment = await self.payment_crud.get_by_payment_reference(payment_reference)
            if payment is None:
                logging.warning(
                    "Payment not found for payment reference %s", payment_reference
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
        except HTTPException:
            raise
        except Exception as error:
            logging.error("Error in PaymentController.get_payment_status: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch payment status.",
            )

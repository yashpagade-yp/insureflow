"""CRUD helpers for payment documents in the provider backend."""

from __future__ import annotations

from datetime import datetime, timezone

from commons.logger import logger
from core.database.database import get_engine
from core.models.payment_model import PaymentModel, PaymentOtp, PaymentStatus

logging = logger(__name__)


class PaymentCrud:
    """Provides database operations for provider payment documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, payment: PaymentModel) -> PaymentModel:
        """Persist a new payment document."""
        try:
            logging.info("Executing PaymentCrud.create function")
            await self.engine.save(payment)
            return payment
        except Exception as error:
            logging.error("Error in PaymentCrud.create function: %s", error)
            raise

    async def get_by_transaction_id(self, transaction_id: str) -> PaymentModel | None:
        """Return one payment by transaction id."""
        try:
            logging.info("Executing PaymentCrud.get_by_transaction_id function")
            return await self.engine.find_one(
                PaymentModel,
                PaymentModel.transaction_id == transaction_id,
            )
        except Exception as error:
            logging.error("Error in PaymentCrud.get_by_transaction_id function: %s", error)
            raise

    async def get_by_payment_reference(self, payment_reference: str) -> PaymentModel | None:
        """Return one payment by business payment reference."""
        try:
            logging.info("Executing PaymentCrud.get_by_payment_reference function")
            return await self.engine.find_one(
                PaymentModel,
                PaymentModel.payment_reference == payment_reference,
            )
        except Exception as error:
            logging.error(
                "Error in PaymentCrud.get_by_payment_reference function: %s", error
            )
            raise

    async def save(self, payment: PaymentModel) -> PaymentModel:
        """Persist an already-mutated payment document."""
        try:
            logging.info("Executing PaymentCrud.save function")
            payment.updated_at = datetime.now(timezone.utc)
            await self.engine.save(payment)
            return payment
        except Exception as error:
            logging.error("Error in PaymentCrud.save function: %s", error)
            raise

    async def save_payment_otp(self, payment: PaymentModel, payment_otp: PaymentOtp) -> PaymentModel:
        """Store or replace the current payment OTP state."""
        try:
            logging.info("Executing PaymentCrud.save_payment_otp function")
            payment.payment_otp = payment_otp
            payment.updated_at = datetime.now(timezone.utc)
            await self.engine.save(payment)
            return payment
        except Exception as error:
            logging.error("Error in PaymentCrud.save_payment_otp function: %s", error)
            raise

    async def mark_success(self, payment: PaymentModel) -> PaymentModel:
        """Mark a payment as successful."""
        try:
            logging.info("Executing PaymentCrud.mark_success function")
            payment.payment_status = PaymentStatus.SUCCESS
            payment.updated_at = datetime.now(timezone.utc)
            await self.engine.save(payment)
            return payment
        except Exception as error:
            logging.error("Error in PaymentCrud.mark_success function: %s", error)
            raise

    async def mark_failed(self, payment: PaymentModel) -> PaymentModel:
        """Mark a payment as failed."""
        try:
            logging.info("Executing PaymentCrud.mark_failed function")
            payment.payment_status = PaymentStatus.FAILED
            payment.updated_at = datetime.now(timezone.utc)
            await self.engine.save(payment)
            return payment
        except Exception as error:
            logging.error("Error in PaymentCrud.mark_failed function: %s", error)
            raise

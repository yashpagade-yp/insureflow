"""CRUD helpers for payment documents in the provider backend."""

from __future__ import annotations

from datetime import datetime, timezone

from ..database.database import get_engine
from ..models.payment_model import PaymentModel, PaymentOtp, PaymentStatus


class PaymentCrud:
    """Provides database operations for provider payment documents."""

    def __init__(self) -> None:
        """Initialise the CRUD helper with the shared ODMantic engine."""

        self.engine = get_engine()

    async def create(self, payment: PaymentModel) -> PaymentModel:
        """Persist a new payment document."""

        await self.engine.save(payment)
        return payment

    async def get_by_transaction_id(self, transaction_id: str) -> PaymentModel | None:
        """Return one payment by transaction id."""

        return await self.engine.find_one(
            PaymentModel,
            PaymentModel.transaction_id == transaction_id,
        )

    async def get_by_payment_reference(self, payment_reference: str) -> PaymentModel | None:
        """Return one payment by business payment reference."""

        return await self.engine.find_one(
            PaymentModel,
            PaymentModel.payment_reference == payment_reference,
        )

    async def save(self, payment: PaymentModel) -> PaymentModel:
        """Persist an already-mutated payment document."""

        payment.updated_at = datetime.now(timezone.utc)
        await self.engine.save(payment)
        return payment

    async def save_payment_otp(self, payment: PaymentModel, payment_otp: PaymentOtp) -> PaymentModel:
        """Store or replace the current payment OTP state."""

        payment.payment_otp = payment_otp
        payment.updated_at = datetime.now(timezone.utc)
        await self.engine.save(payment)
        return payment

    async def mark_success(self, payment: PaymentModel) -> PaymentModel:
        """Mark a payment as successful."""

        payment.payment_status = PaymentStatus.SUCCESS
        payment.updated_at = datetime.now(timezone.utc)
        await self.engine.save(payment)
        return payment

    async def mark_failed(self, payment: PaymentModel) -> PaymentModel:
        """Mark a payment as failed."""

        payment.payment_status = PaymentStatus.FAILED
        payment.updated_at = datetime.now(timezone.utc)
        await self.engine.save(payment)
        return payment

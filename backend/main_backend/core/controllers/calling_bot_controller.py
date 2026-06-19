"""Controller logic for customer-app calling-bot flows."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from commons.logger import logger
from core.apis.schemas.request_schema.calling_bot_request_schema import (
    CallingBotCompletePurchaseRequest,
    CallingBotPreparePurchaseRequest,
    CallingBotStartCallRequest,
)
from core.apis.schemas.request_schema.insurance_detail_request_schema import (
    InsuranceDetailCreateRequest,
)
from core.apis.schemas.request_schema.payment_request_schema import (
    PaymentCreateRequest,
    PaymentOtpVerifyRequest,
)
from core.apis.schemas.request_schema.quote_request_schema import (
    QuoteSelectAddOnsRequest,
    QuoteSelectPlanRequest,
    QuoteSelectedAddOnRequest,
)
from core.apis.schemas.response_schema.calling_bot_response_schema import (
    CallingBotCallDetailResponse,
    CallingBotCallListResponse,
    CallingBotCallResponse,
    CallingBotCompletePurchaseResponse,
    CallingBotConfigResponse,
    CallingBotPlanResponse,
    CallingBotPreparePurchaseResponse,
    CallingBotStartCallResponse,
)
from core.controllers.insurance_detail_controller import InsuranceDetailController
from core.controllers.payment_controller import PaymentController
from core.controllers.policy_controller import PolicyController
from core.controllers.quote_controller import QuoteController
from core.controllers.transaction_controller import TransactionController
from core.cruds.calling_bot_crud import CallingBotCrud
from core.models.calling_bot_model import (
    CallingBotCallModel,
    CallStatus,
    CustomerInterestStatus,
    PolicyEmailStatus,
    RecommendedPlanSnapshot,
)
from core.services.twilio_voice_service import TwilioVoiceService

logging = logger(__name__)


class CallingBotController:
    """Handles admin-triggered outbound calling-bot flows."""

    def __init__(self) -> None:
        """Initialise the controller with its dependencies."""

        self.calling_bot_crud = CallingBotCrud()
        self.twilio_voice_service = TwilioVoiceService()
        self.insurance_detail_controller = InsuranceDetailController()
        self.quote_controller = QuoteController()
        self.transaction_controller = TransactionController()
        self.payment_controller = PaymentController()
        self.policy_controller = PolicyController()

    async def get_safe_config(self) -> CallingBotConfigResponse:
        """Return safe configuration details for the frontend bot section."""

        logging.info("Executing CallingBotController.get_safe_config function")
        return CallingBotConfigResponse(**self.twilio_voice_service.build_safe_config())

    async def start_outbound_call(
        self,
        payload: CallingBotStartCallRequest,
        admin_id: str,
        admin_email: str,
    ) -> CallingBotStartCallResponse:
        """Create one call record and start an outbound Twilio call."""

        try:
            logging.info("Executing CallingBotController.start_outbound_call function")
            customer_name = payload.customer_name.strip()
            customer_phone = self._normalize_phone(payload.customer_phone)
            customer_email = payload.customer_email.strip() if payload.customer_email else None
            if not customer_name or not customer_phone:
                logging.warning("Calling-bot start call received empty customer values")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer name and phone number are required.",
                )

            call_record = await self.calling_bot_crud.create(
                CallingBotCallModel.model_validate(
                    {
                        "customer_name": customer_name,
                        "customer_phone": customer_phone,
                        "customer_email": customer_email,
                        "desired_coverage_amount": payload.desired_coverage_amount,
                        "started_by_admin_id": admin_id,
                        "started_by_admin_email": admin_email,
                        "from_number": self.twilio_voice_service.from_number or None,
                        "summary": payload.notes.strip() if payload.notes else None,
                        "transcript_lines": [
                            "Call created by customer-app admin.",
                            "Outbound call will introduce InsureFlow and capture customer interest.",
                        ],
                    }
                )
            )

            twilio_response = self.twilio_voice_service.create_outbound_call(
                customer_phone=customer_phone,
                call_reference=call_record.call_reference,
            )

            mapped_status = self._map_twilio_status_to_call_status(
                str(twilio_response.get("status") or "initiated")
            )
            call_record = await self.calling_bot_crud.update(
                call_record,
                {
                    "call_sid": twilio_response.get("call_sid"),
                    "status": mapped_status,
                    "from_number": twilio_response.get("from_number"),
                    "transcript_lines": [
                        *call_record.transcript_lines,
                        f"Twilio outbound call created with status {mapped_status.value}.",
                    ],
                },
            )

            return CallingBotStartCallResponse(
                message="Outbound calling-bot call started successfully.",
                call_reference=call_record.call_reference,
                call_sid=call_record.call_sid,
                status=call_record.status.value,
                from_number=call_record.from_number,
                to_number=call_record.customer_phone,
                created_at=call_record.created_at,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in CallingBotController.start_outbound_call function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in CallingBotController.start_outbound_call function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start the calling-bot outbound call.",
            )

    async def list_calls(self) -> CallingBotCallListResponse:
        """Return all stored calling-bot call summaries."""

        try:
            logging.info("Executing CallingBotController.list_calls function")
            items = await self.calling_bot_crud.list_all()
            return CallingBotCallListResponse(
                items=[self._build_call_summary(item) for item in items],
                total_count=len(items),
            )
        except HTTPException as httperror:
            logging.error("Error in CallingBotController.list_calls function: %s", httperror)
            raise httperror
        except Exception as error:
            logging.error("Error in CallingBotController.list_calls function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list calling-bot calls.",
            )

    async def get_call_detail(self, call_reference: str) -> CallingBotCallDetailResponse:
        """Return one detailed calling-bot call record."""

        try:
            logging.info("Executing CallingBotController.get_call_detail function")
            call_record = await self._get_call_record(call_reference)
            return self._build_call_detail(call_record)
        except HTTPException as httperror:
            logging.error(
                "Error in CallingBotController.get_call_detail function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in CallingBotController.get_call_detail function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch the calling-bot call details.",
            )

    async def build_initial_twiml(self, call_reference: str) -> str:
        """Return the first TwiML response for the outbound bot call."""

        call_record = await self._get_call_record(call_reference)
        interest_action_url = (
            f"{self.twilio_voice_service.webhook_base_url}/v1/calling-bot/twiml/outbound/"
            f"{call_reference}/interest"
        )
        return self.twilio_voice_service.build_initial_voice_response(
            call_record.customer_name,
            interest_action_url,
        )

    async def process_interest_response(
        self,
        call_reference: str,
        digits: str | None,
        speech_result: str | None,
    ) -> str:
        """Process customer interest response and return next TwiML markup."""

        call_record = await self._get_call_record(call_reference)
        interpreted_interest = self._interpret_interest(digits, speech_result)
        transcript_line = "Customer interest response could not be understood."
        if interpreted_interest == CustomerInterestStatus.INTERESTED:
            transcript_line = "Customer confirmed this is a good time to continue."
        elif interpreted_interest == CustomerInterestStatus.NOT_INTERESTED:
            transcript_line = "Customer requested to stop or continue later."

        call_record = await self.calling_bot_crud.update(
            call_record,
            {
                "customer_interest": interpreted_interest,
                "status": CallStatus.IN_PROGRESS,
                "transcript_lines": [*call_record.transcript_lines, transcript_line],
            },
        )

        if interpreted_interest == CustomerInterestStatus.UNKNOWN:
            return self.twilio_voice_service.build_interest_retry_response(
                interest_action_url=(
                    f"{self.twilio_voice_service.webhook_base_url}/v1/calling-bot/twiml/outbound/"
                    f"{call_reference}/interest"
                )
            )
        if interpreted_interest == CustomerInterestStatus.NOT_INTERESTED:
            return self.twilio_voice_service.build_polite_exit_response()
        coverage_action_url = (
            f"{self.twilio_voice_service.webhook_base_url}/v1/calling-bot/twiml/outbound/"
            f"{call_reference}/coverage"
        )
        return self.twilio_voice_service.build_interest_capture_response(
            coverage_action_url
        )

    async def process_coverage_response(
        self,
        call_reference: str,
        digits: str | None,
        speech_result: str | None,
    ) -> str:
        """Capture coverage amount, generate quotes, and return plan-summary TwiML."""

        call_record = await self._get_call_record(call_reference)
        try:
            logging.info(
                "Executing CallingBotController.process_coverage_response function"
            )
            coverage_amount = self._extract_coverage_amount(digits, speech_result)
            if coverage_amount is None:
                await self.calling_bot_crud.update(
                    call_record,
                    {
                        "transcript_lines": [
                            *call_record.transcript_lines,
                            "Coverage amount was not captured successfully.",
                        ],
                    },
                )
                coverage_action_url = (
                    f"{self.twilio_voice_service.webhook_base_url}/v1/calling-bot/twiml/outbound/"
                    f"{call_reference}/coverage"
                )
                return self.twilio_voice_service.build_interest_capture_response(
                    coverage_action_url=coverage_action_url,
                    retry=True,
                )

            journey_response = await self.insurance_detail_controller.create_insurance_detail_journey(
                InsuranceDetailCreateRequest(
                    mobile_number=self._strip_country_prefix(call_record.customer_phone),
                    insurance_type="health",
                    proposer_first_name=self._extract_first_name(call_record.customer_name),
                    proposer_last_name=self._extract_last_name(call_record.customer_name),
                    proposer_email=call_record.customer_email,
                    sum_insured_requested=coverage_amount,
                    form_step="calling-bot",
                    is_form_completed=True,
                    insured_members=[],
                    existing_insurance_details={},
                    medical_history={},
                    additional_answers={},
                )
            )
            quote_response = await self.quote_controller.get_quotes(
                journey_response.transaction_id
            )
            recommended_plans = [
                RecommendedPlanSnapshot.model_validate(
                    {
                        "plan_id": item.plan_id,
                        "company_name": item.company_name,
                        "plan_name": item.plan_name,
                        "coverage_amount": item.coverage_amount,
                        "total_premium": item.total_premium,
                    }
                )
                for item in quote_response.items
                if item.coverage_amount <= coverage_amount
            ]
            recommended_plans = sorted(
                recommended_plans,
                key=lambda item: item.total_premium,
            )[:3]

            plan_summary_lines = [
                (
                    f"Option {index + 1}. {item.plan_name} from {item.company_name}. "
                    f"Coverage is about rupees {int(item.coverage_amount):,}. "
                    f"Premium is about rupees {int(item.total_premium):,}."
                )
                for index, item in enumerate(recommended_plans)
            ]
            summary = (
                f"Customer requested approximately Rs. {int(coverage_amount):,} coverage. "
                f"{len(recommended_plans)} matching plans were prepared."
            )
            await self.calling_bot_crud.update(
                call_record,
                {
                    "desired_coverage_amount": coverage_amount,
                    "recommended_plans": recommended_plans,
                    "transaction_id": journey_response.transaction_id,
                    "user_id": journey_response.user_id,
                    "summary": summary,
                    "transcript_lines": [
                        *call_record.transcript_lines,
                        f"Captured coverage amount: {coverage_amount}.",
                        f"Prepared {len(recommended_plans)} matching plans from the database.",
                    ],
                },
            )
            return self.twilio_voice_service.build_plan_summary_response(
                plan_summary_lines
            )
        except HTTPException as httperror:
            logging.error(
                "Error in CallingBotController.process_coverage_response function: %s",
                httperror,
            )
            await self.calling_bot_crud.update(
                call_record,
                {
                    "last_error": (
                        httperror.detail
                        if isinstance(httperror.detail, str)
                        else "Coverage processing failed."
                    ),
                    "transcript_lines": [
                        *call_record.transcript_lines,
                        "Coverage processing failed during the call.",
                    ],
                },
            )
            return self.twilio_voice_service.build_plan_summary_response([])
        except Exception as error:
            logging.error(
                "Error in CallingBotController.process_coverage_response function: %s",
                error,
            )
            await self.calling_bot_crud.update(
                call_record,
                {
                    "last_error": "Unexpected coverage processing failure.",
                    "transcript_lines": [
                        *call_record.transcript_lines,
                        "Unexpected coverage processing failure occurred.",
                    ],
                },
            )
            return self.twilio_voice_service.build_plan_summary_response([])

    async def update_call_status_from_callback(
        self,
        call_reference: str,
        callback_payload: dict[str, Any],
    ) -> None:
        """Persist Twilio status-callback data on one stored call record."""

        try:
            logging.info(
                "Executing CallingBotController.update_call_status_from_callback function"
            )
            call_record = await self._get_call_record(call_reference)
            raw_status = callback_payload.get("CallStatus") or callback_payload.get(
                "callstatus"
            )
            call_status = self._map_twilio_status_to_call_status(str(raw_status or ""))
            updates: dict[str, Any] = {"status": call_status}
            if callback_payload.get("CallSid"):
                updates["call_sid"] = str(callback_payload["CallSid"])
            if callback_payload.get("CallDuration"):
                try:
                    updates["duration_seconds"] = int(callback_payload["CallDuration"])
                except Exception:
                    logging.warning(
                        "Invalid CallDuration received for call %s",
                        call_reference,
                    )
            transcript_lines = [
                *call_record.transcript_lines,
                f"Twilio callback received with status {call_status.value}.",
            ]
            updates["transcript_lines"] = transcript_lines
            if call_status in {
                CallStatus.COMPLETED,
                CallStatus.FAILED,
                CallStatus.NO_ANSWER,
                CallStatus.BUSY,
                CallStatus.CANCELED,
            }:
                updates["completed_at"] = datetime.now(timezone.utc)
            await self.calling_bot_crud.update(call_record, updates)
        except Exception as error:
            logging.error(
                "Error in CallingBotController.update_call_status_from_callback function: %s",
                error,
            )

    async def prepare_purchase(
        self,
        call_reference: str,
        payload: CallingBotPreparePurchaseRequest,
    ) -> CallingBotPreparePurchaseResponse:
        """Prepare payment and generate the mock OTP for one bot purchase."""

        try:
            logging.info("Executing CallingBotController.prepare_purchase function")
            call_record = await self._get_call_record(call_reference)
            selected_item = await self._get_selected_quote_item(
                call_record,
                payload.selected_plan_id,
            )

            await self._select_plan_and_add_ons_for_call(call_record, selected_item)
            payment_response = await self.payment_controller.create_payment(
                PaymentCreateRequest(
                    transaction_id=call_record.transaction_id,
                    user_id=call_record.user_id,
                    amount=selected_item.total_premium,
                )
            )
            payment_otp_response = await self.payment_controller.send_payment_otp(
                payment_response.payment_reference
            )
            updated_call_record = await self.calling_bot_crud.update(
                call_record,
                {
                    "selected_plan_id": selected_item.plan_id,
                    "selected_plan_name": selected_item.plan_name,
                    "provider_company_name": selected_item.company_name,
                    "payment_reference": payment_response.payment_reference,
                    "payment_status": payment_response.payment_status,
                    "status": CallStatus.IN_PROGRESS,
                    "summary": "Payment OTP generated for calling-bot purchase confirmation.",
                    "last_error": None,
                    "transcript_lines": [
                        *call_record.transcript_lines,
                        f"Customer selected {selected_item.plan_name}.",
                        "Mock payment OTP generated for admin-assisted confirmation.",
                    ],
                },
            )
            return CallingBotPreparePurchaseResponse(
                message="Calling-bot payment OTP prepared successfully.",
                call_reference=updated_call_record.call_reference,
                transaction_id=updated_call_record.transaction_id,
                selected_plan_id=selected_item.plan_id,
                selected_plan_name=selected_item.plan_name,
                provider_company_name=selected_item.company_name,
                payment_reference=payment_response.payment_reference,
                payment_status=payment_response.payment_status,
                otp_expires_at=payment_otp_response.otp_expires_at,
                plain_otp=payment_otp_response.plain_otp,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in CallingBotController.prepare_purchase function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in CallingBotController.prepare_purchase function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to prepare the calling-bot purchase flow.",
            )

    async def complete_purchase(
        self,
        call_reference: str,
        payload: CallingBotCompletePurchaseRequest,
    ) -> CallingBotCompletePurchaseResponse:
        """Complete the purchase flow for a calling-bot call using mock OTP."""

        try:
            logging.info("Executing CallingBotController.complete_purchase function")
            call_record = await self._get_call_record(call_reference)
            if not call_record.transaction_id or not call_record.user_id:
                logging.warning(
                    "Call %s has no generated customer journey to complete purchase",
                    call_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This call has not generated a customer journey yet.",
                )
            if not call_record.payment_reference:
                logging.warning(
                    "Call %s attempted purchase completion before OTP preparation",
                    call_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Prepare the payment OTP first before completing the purchase.",
                )
            if (
                call_record.selected_plan_id
                and call_record.selected_plan_id != payload.selected_plan_id.strip()
            ):
                logging.warning(
                    "Call %s attempted OTP completion with mismatched selected plan",
                    call_reference,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected plan does not match the prepared payment flow.",
                )

            verification_response = await self.payment_controller.verify_payment_otp(
                PaymentOtpVerifyRequest(
                    transaction_id=call_record.transaction_id,
                    payment_reference=call_record.payment_reference,
                    otp=payload.payment_otp.strip(),
                )
            )
            policy_response = await self.policy_controller.get_policy(
                verification_response.policy_number
            )
            updated_call_record = await self.calling_bot_crud.update(
                call_record,
                {
                    "payment_status": verification_response.payment_status,
                    "policy_number": verification_response.policy_number,
                    "policy_pdf_url": policy_response.pdf_url,
                    "policy_email_status": (
                        PolicyEmailStatus.SENT
                        if call_record.customer_email
                        else PolicyEmailStatus.NOT_TRIGGERED
                    ),
                    "status": CallStatus.COMPLETED,
                    "completed_at": datetime.now(timezone.utc),
                    "summary": "Calling-bot purchase completed successfully.",
                    "last_error": None,
                    "transcript_lines": [
                        *call_record.transcript_lines,
                        "Mock payment OTP was verified successfully.",
                        f"Policy {verification_response.policy_number} was issued successfully.",
                    ],
                },
            )
            return CallingBotCompletePurchaseResponse(
                message="Calling-bot purchase completed successfully.",
                call_reference=updated_call_record.call_reference,
                transaction_id=updated_call_record.transaction_id,
                selected_plan_id=updated_call_record.selected_plan_id,
                payment_reference=updated_call_record.payment_reference,
                payment_status=verification_response.payment_status,
                policy_number=verification_response.policy_number,
                policy_pdf_url=policy_response.pdf_url,
                policy_email_status=updated_call_record.policy_email_status.value,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in CallingBotController.complete_purchase function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in CallingBotController.complete_purchase function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to complete the calling-bot purchase flow.",
            )

    async def _get_call_record(self, call_reference: str) -> CallingBotCallModel:
        """Return one call record by reference or raise a not-found error."""

        normalized_call_reference = call_reference.strip()
        if not normalized_call_reference:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Call reference is required.",
            )
        call_record = await self.calling_bot_crud.get_by_call_reference(
            normalized_call_reference
        )
        if call_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calling-bot call not found.",
            )
        return call_record

    def _build_call_summary(
        self,
        call_record: CallingBotCallModel,
    ) -> CallingBotCallResponse:
        """Convert one call document into the list-view response schema."""

        return CallingBotCallResponse(
            call_reference=call_record.call_reference,
            call_sid=call_record.call_sid,
            customer_name=call_record.customer_name,
            customer_phone=call_record.customer_phone,
            direction=call_record.direction.value,
            calling_type=call_record.calling_type,
            status=call_record.status.value,
            customer_interest=call_record.customer_interest.value,
            desired_coverage_amount=call_record.desired_coverage_amount,
            duration_seconds=call_record.duration_seconds,
            recommended_plan_count=len(call_record.recommended_plans),
            selected_plan_name=call_record.selected_plan_name,
            policy_number=call_record.policy_number,
            policy_email_status=call_record.policy_email_status.value,
            created_at=call_record.created_at,
            updated_at=call_record.updated_at,
        )

    def _build_call_detail(
        self,
        call_record: CallingBotCallModel,
    ) -> CallingBotCallDetailResponse:
        """Convert one call document into the detailed frontend response."""

        return CallingBotCallDetailResponse(
            call_reference=call_record.call_reference,
            call_sid=call_record.call_sid,
            customer_name=call_record.customer_name,
            customer_phone=call_record.customer_phone,
            customer_email=call_record.customer_email,
            direction=call_record.direction.value,
            calling_type=call_record.calling_type,
            status=call_record.status.value,
            customer_interest=call_record.customer_interest.value,
            desired_coverage_amount=call_record.desired_coverage_amount,
            transaction_id=call_record.transaction_id,
            user_id=call_record.user_id,
            selected_plan_id=call_record.selected_plan_id,
            selected_plan_name=call_record.selected_plan_name,
            provider_company_name=call_record.provider_company_name,
            payment_reference=call_record.payment_reference,
            payment_status=call_record.payment_status,
            policy_number=call_record.policy_number,
            policy_pdf_url=call_record.policy_pdf_url,
            policy_email_status=call_record.policy_email_status.value,
            duration_seconds=call_record.duration_seconds,
            from_number=call_record.from_number,
            summary=call_record.summary,
            transcript_lines=call_record.transcript_lines,
            recommended_plans=[
                CallingBotPlanResponse(
                    plan_id=item.plan_id,
                    company_name=item.company_name,
                    plan_name=item.plan_name,
                    coverage_amount=item.coverage_amount,
                    total_premium=item.total_premium,
                )
                for item in call_record.recommended_plans
            ],
            last_error=call_record.last_error,
            started_by_admin_id=call_record.started_by_admin_id,
            started_by_admin_email=call_record.started_by_admin_email,
            created_at=call_record.created_at,
            updated_at=call_record.updated_at,
            completed_at=call_record.completed_at,
        )

    def _normalize_phone(self, value: str) -> str:
        """Normalize a customer phone number into E.164 format when possible."""

        digits = "".join(character for character in value if character.isdigit())
        if not digits:
            return ""
        if digits.startswith("91") and len(digits) == 12:
            return f"+{digits}"
        if len(digits) == 10:
            return f"+91{digits}"
        if value.strip().startswith("+"):
            return value.strip()
        return f"+{digits}"

    def _strip_country_prefix(self, value: str) -> str:
        """Strip an Indian +91 country prefix for internal mobile-number reuse."""

        digits = "".join(character for character in value if character.isdigit())
        if digits.startswith("91") and len(digits) == 12:
            return digits[2:]
        return digits

    def _extract_first_name(self, full_name: str) -> str:
        """Return the first token from a full name."""

        parts = full_name.split()
        return parts[0] if parts else "Customer"

    def _extract_last_name(self, full_name: str) -> str:
        """Return the remaining tokens from a full name."""

        parts = full_name.split()
        if len(parts) <= 1:
            return "User"
        return " ".join(parts[1:])

    def _interpret_interest(
        self,
        digits: str | None,
        speech_result: str | None,
    ) -> CustomerInterestStatus:
        """Interpret the customer interest capture from speech or keypad input."""

        normalized_digits = (digits or "").strip()
        normalized_speech = (speech_result or "").strip().lower()
        if normalized_digits == "1":
            return CustomerInterestStatus.INTERESTED
        if normalized_digits == "2":
            return CustomerInterestStatus.NOT_INTERESTED
        if any(
            token in normalized_speech
            for token in ["yes", "interested", "buy", "okay", "ok", "sure", "continue", "go ahead"]
        ):
            return CustomerInterestStatus.INTERESTED
        if any(
            token in normalized_speech
            for token in ["later", "no", "not now", "busy", "call later"]
        ):
            return CustomerInterestStatus.NOT_INTERESTED
        return CustomerInterestStatus.UNKNOWN

    def _extract_coverage_amount(
        self,
        digits: str | None,
        speech_result: str | None,
    ) -> float | None:
        """Extract a coverage amount from keypad or speech input."""

        normalized_digits = "".join(
            character for character in (digits or "") if character.isdigit()
        )
        if normalized_digits:
            return float(normalized_digits)

        normalized_speech = (speech_result or "").strip().lower()
        lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*lakh", normalized_speech)
        if lakh_match:
            return float(lakh_match.group(1)) * 100000

        numeric_match = re.search(r"(\d{5,8})", normalized_speech.replace(",", ""))
        if numeric_match:
            return float(numeric_match.group(1))

        word_map = {
            "three lakh": 300000.0,
            "five lakh": 500000.0,
            "ten lakh": 1000000.0,
            "fifteen lakh": 1500000.0,
        }
        for phrase, amount in word_map.items():
            if phrase in normalized_speech:
                return amount
        return None

    def _map_twilio_status_to_call_status(self, value: str) -> CallStatus:
        """Map a Twilio call status into the local enum."""

        normalized_value = value.strip().lower()
        mapping = {
            "queued": CallStatus.QUEUED,
            "initiated": CallStatus.INITIATED,
            "ringing": CallStatus.RINGING,
            "in-progress": CallStatus.IN_PROGRESS,
            "in_progress": CallStatus.IN_PROGRESS,
            "answered": CallStatus.IN_PROGRESS,
            "completed": CallStatus.COMPLETED,
            "failed": CallStatus.FAILED,
            "no-answer": CallStatus.NO_ANSWER,
            "no_answer": CallStatus.NO_ANSWER,
            "busy": CallStatus.BUSY,
            "canceled": CallStatus.CANCELED,
        }
        return mapping.get(normalized_value, CallStatus.QUEUED)

    async def _get_selected_quote_item(
        self,
        call_record: CallingBotCallModel,
        selected_plan_id: str,
    ) -> Any:
        """Return the selected quote item for one prepared bot purchase."""

        if not call_record.transaction_id or not call_record.user_id:
            logging.warning(
                "Call %s has no generated customer journey",
                call_record.call_reference,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This call has not generated a customer journey yet.",
            )

        quote_response = await self.quote_controller.get_quotes(call_record.transaction_id)
        normalized_plan_id = selected_plan_id.strip()
        selected_item = next(
            (item for item in quote_response.items if item.plan_id == normalized_plan_id),
            None,
        )
        if selected_item is None:
            logging.warning(
                "Selected plan %s not found on call %s",
                selected_plan_id,
                call_record.call_reference,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected plan not found for this call.",
            )
        return selected_item

    async def _select_plan_and_add_ons_for_call(
        self,
        call_record: CallingBotCallModel,
        selected_item: Any,
    ) -> None:
        """Persist selected plan and add-ons before the payment step."""

        await self.transaction_controller.select_plan(
            QuoteSelectPlanRequest(
                transaction_id=call_record.transaction_id,
                selected_plan_id=selected_item.plan_id,
            )
        )
        await self.transaction_controller.save_selected_add_ons(
            QuoteSelectAddOnsRequest(
                transaction_id=call_record.transaction_id,
                selected_plan_id=selected_item.plan_id,
                selected_add_ons=[
                    QuoteSelectedAddOnRequest(name=item.name, price=item.price)
                    for item in selected_item.selected_add_ons
                ],
            )
        )

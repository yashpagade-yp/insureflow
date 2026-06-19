"""Twilio voice helpers for the main-backend calling-bot flow."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException, status
from twilio.rest import Client
from twilio.twiml.voice_response import Gather, VoiceResponse

from commons.logger import logger

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

logging = logger(__name__)


def _normalize_base_url(url: str) -> str:
    """Normalize a configured base URL by trimming trailing slashes."""

    return url.rstrip("/")


class TwilioVoiceService:
    """Encapsulates Twilio client usage for outbound calling-bot actions."""

    def __init__(self) -> None:
        """Initialise the service from the configured environment."""

        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER", "").strip()
        self.test_to_number = os.getenv("TWILIO_TEST_TO_NUMBER", "").strip()
        self.say_voice = os.getenv("TWILIO_SAY_VOICE", "").strip()
        self.say_language = os.getenv("TWILIO_SAY_LANGUAGE", "").strip()
        self.gather_language = os.getenv("TWILIO_GATHER_LANGUAGE", "en-IN").strip()
        self.webhook_base_url = _normalize_base_url(
            os.getenv("MAIN_BACKEND_PUBLIC_URL", "http://127.0.0.1:8000").strip()
        )

    def build_safe_config(self) -> dict[str, str | bool | list[str] | None]:
        """Return a safe, frontend-readable Twilio/calling-bot configuration."""

        masked_sid = None
        if self.account_sid:
            masked_sid = f"{self.account_sid[:6]}...{self.account_sid[-4:]}"

        return {
            "bot_name": "InsureFlow Calling Bot",
            "channel": "Twilio Voice",
            "mode": "outbound-only",
            "trigger_owner": "customer-app admin",
            "backend_name": "main_backend",
            "twilio_from_number": self.from_number or None,
            "twilio_test_to_number": self.test_to_number or None,
            "masked_account_sid": masked_sid,
            "auth_token_configured": bool(self.auth_token),
            "webhook_base_url": self.webhook_base_url or None,
            "conversation_steps": [
                "Introduce InsureFlow clearly and explain why the customer is being called",
                "Ask whether it is a good time to continue",
                "Capture the desired coverage amount with short examples",
                "Recommend matching plans from the database in simple language",
                "Hand off the next purchase step for payment OTP and policy delivery",
            ],
        }

    def validate_required_credentials(self) -> None:
        """Ensure Twilio credentials are configured before outbound call actions."""

        if not self.account_sid or not self.auth_token or not self.from_number:
            logging.error("Twilio credentials are missing in main_backend/.env")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Twilio calling credentials are not fully configured.",
            )

    def create_outbound_call(
        self,
        customer_phone: str,
        call_reference: str,
    ) -> dict[str, str | None]:
        """Create one outbound Twilio voice call for the calling-bot flow."""

        self.validate_required_credentials()
        twiml_url = (
            f"{self.webhook_base_url}/v1/calling-bot/twiml/outbound/{call_reference}"
        )
        status_callback_url = (
            f"{self.webhook_base_url}/v1/calling-bot/calls/status/{call_reference}"
        )

        try:
            logging.info(
                "Creating Twilio outbound call for call_reference %s to %s",
                call_reference,
                customer_phone,
            )
            client = Client(self.account_sid, self.auth_token)
            call = client.calls.create(
                to=customer_phone,
                from_=self.from_number,
                url=twiml_url,
                method="POST",
                status_callback=status_callback_url,
                status_callback_method="POST",
                status_callback_event=["initiated", "ringing", "answered", "completed"],
            )
            return {
                "call_sid": call.sid,
                "status": getattr(call, "status", None),
                "from_number": self.from_number,
                "to_number": customer_phone,
            }
        except Exception as error:
            logging.error(
                "Failed to create Twilio outbound call for %s: %s",
                call_reference,
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to start the outbound Twilio call.",
            )

    def build_initial_voice_response(
        self,
        customer_name: str,
        interest_action_url: str,
    ) -> str:
        """Build the initial TwiML greeting and interest question."""

        response = VoiceResponse()
        self._append_say_lines(
            response,
            [
                f"Hello {customer_name}.",
                "This is InsureFlow calling.",
                "We help customers compare health insurance plans, understand coverage, and complete policy support.",
                "This will take less than two minutes.",
            ],
        )
        gather = self._build_speech_gather(
            action_url=interest_action_url,
            num_digits=1,
            hints="yes, no, later, continue, call later, health insurance, policy",
        )
        self._append_say_lines(
            gather,
            [
                "If this is a good time, press 1 or say yes.",
                "If you want us to call later, press 2 or say later.",
            ],
        )
        response.append(gather)
        self._append_say_lines(
            response,
            [
                "I could not hear a clear response.",
                "Please try again when you are ready.",
            ],
        )
        response.hangup()
        return str(response)

    def build_interest_capture_response(
        self,
        coverage_action_url: str,
        retry: bool = False,
    ) -> str:
        """Build the TwiML prompt that captures desired coverage amount."""

        response = VoiceResponse()
        if retry:
            self._append_say_lines(
                response,
                [
                    "Sorry, I did not catch the coverage amount clearly.",
                    "Please say only the amount you want.",
                ],
            )
        else:
            self._append_say_lines(
                response,
                [
                    "Thank you.",
                    "I will ask one simple question at a time.",
                ],
            )
        gather = self._build_speech_gather(
            action_url=coverage_action_url,
            hints="three lakh, five lakh, ten lakh, fifteen lakh, 300000, 500000, 1000000, 1500000",
        )
        self._append_say_lines(
            gather,
            [
                "What coverage amount would you like me to search for?",
                "For example, you can say five lakh, ten lakh, or fifteen lakh.",
            ],
        )
        response.append(gather)
        self._append_say_lines(
            response,
            [
                "I still could not capture the amount clearly.",
                "Our team can follow up with you later.",
            ],
        )
        response.hangup()
        return str(response)

    def build_plan_summary_response(self, plan_summaries: list[str]) -> str:
        """Build the TwiML response that reads matched plan summaries."""

        response = VoiceResponse()
        if not plan_summaries:
            self._append_say_lines(
                response,
                [
                    "I could not prepare a matching plan right now.",
                    "Our InsureFlow team will review your request and help you continue the journey.",
                    "Thank you for your time.",
                ],
            )
        else:
            self._append_say_lines(
                response,
                [
                    "Thank you.",
                    "Based on what you told me, I found a few suitable options.",
                ],
            )
            for item in plan_summaries[:2]:
                self._append_say_lines(response, [item])
            self._append_say_lines(
                response,
                [
                    "Your matching plans are now ready in the InsureFlow system.",
                    "Our admin team can continue the next step with you, including customer details, payment confirmation, and policy email delivery.",
                    "Thank you for speaking with InsureFlow.",
                ],
            )
        response.hangup()
        return str(response)

    def build_interest_retry_response(self, interest_action_url: str) -> str:
        """Build a retry prompt when the first interest response is unclear."""

        response = VoiceResponse()
        self._append_say_lines(
            response,
            [
                "Sorry, I did not catch that clearly.",
                "Please answer with yes to continue, or later if you want a callback.",
            ],
        )
        gather = self._build_speech_gather(
            action_url=interest_action_url,
            num_digits=1,
            hints="yes, no, later, continue, call later",
        )
        self._append_say_lines(
            gather,
            [
                "Press 1 or say yes to continue now.",
                "Press 2 or say later for a later call.",
            ],
        )
        response.append(gather)
        self._append_say_lines(
            response,
            [
                "I am ending this call for now.",
                "Please feel free to continue later.",
            ],
        )
        response.hangup()
        return str(response)

    def build_polite_exit_response(self) -> str:
        """Build the polite closing response when the customer declines."""

        response = VoiceResponse()
        self._append_say_lines(
            response,
            [
                "No problem.",
                "Thank you for your time.",
                "We will be available whenever you want to continue your insurance journey.",
            ],
        )
        response.hangup()
        return str(response)

    def _build_speech_gather(
        self,
        action_url: str,
        num_digits: int | None = None,
        hints: str | None = None,
    ) -> Gather:
        """Build a Gather verb configured for clearer phone conversations."""

        gather_kwargs: dict[str, Any] = {
            "input": "speech dtmf",
            "timeout": 5,
            "speech_timeout": "auto",
            "action": action_url,
            "method": "POST",
            "action_on_empty_result": True,
        }
        if self.gather_language:
            gather_kwargs["language"] = self.gather_language
        if hints:
            gather_kwargs["hints"] = hints
        if num_digits is not None:
            gather_kwargs["num_digits"] = num_digits
        return Gather(**gather_kwargs)

    def _append_say_lines(
        self,
        container: VoiceResponse | Gather,
        lines: list[str],
    ) -> None:
        """Append short speech chunks for better clarity and pacing."""

        for index, line in enumerate(lines):
            if line.strip():
                container.say(line.strip(), **self._say_kwargs())
            if index != len(lines) - 1 and isinstance(container, VoiceResponse):
                container.pause(length=1)

    def _say_kwargs(self) -> dict[str, str]:
        """Return optional voice settings for spoken call responses."""

        options: dict[str, str] = {}
        if self.say_voice:
            options["voice"] = self.say_voice
        if self.say_language:
            options["language"] = self.say_language
        return options

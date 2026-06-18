"""Email delivery helpers for the provider backend."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

from commons.logger import logger

ENV_FILE_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_FILE_PATH)

logging = logger(__name__)

SMTP_HOST = os.environ.get("EMAIL_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD") or os.environ.get("AAP_PASSWORD")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "InsureFlow")


def send_admin_otp_email(recipient_email: str, otp: str) -> None:
    """Send a provider-admin login OTP email through the configured SMTP account."""

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise RuntimeError(
            "Email sender configuration is missing in provider_backend/.env"
        )

    message = EmailMessage()
    message["Subject"] = "InsureFlow Provider Admin Login OTP"
    message["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_ADDRESS}>"
    message["To"] = recipient_email
    message.set_content(
        "\n".join(
            [
                "Your InsureFlow provider-admin login OTP is below.",
                "",
                f"OTP: {otp}",
                "",
                "This OTP expires in 10 minutes.",
                "If you did not request this OTP, please ignore this email.",
            ]
        )
    )

    try:
        logging.info("Sending provider-admin OTP email to %s", recipient_email)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(message)
        logging.info(
            "Provider-admin OTP email sent successfully to %s",
            recipient_email,
        )
    except Exception as error:
        logging.error(
            "Failed to send provider-admin OTP email to %s: %s",
            recipient_email,
            error,
        )
        raise

"""Email delivery helpers for the main backend."""

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
    """Send an admin login OTP email through the configured SMTP account."""

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise RuntimeError("Email sender configuration is missing in main_backend/.env")

    message = EmailMessage()
    message["Subject"] = "InsureFlow Admin Login OTP"
    message["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_ADDRESS}>"
    message["To"] = recipient_email
    message.set_content(
        "\n".join(
            [
                "Your InsureFlow admin login OTP is below.",
                "",
                f"OTP: {otp}",
                "",
                "This OTP expires in 10 minutes.",
                "If you did not request this OTP, please ignore this email.",
            ]
        )
    )

    try:
        logging.info("Sending admin OTP email to %s", recipient_email)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(message)
        logging.info("Admin OTP email sent successfully to %s", recipient_email)
    except Exception as error:
        logging.error("Failed to send admin OTP email to %s: %s", recipient_email, error)
        raise


def send_policy_document_email(
    recipient_email: str,
    policy_number: str,
    company_name: str,
    plan_name: str,
    pdf_file_path: str | None = None,
    pdf_url: str | None = None,
) -> None:
    """Send a policy-issued email with the generated policy PDF when available."""

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise RuntimeError("Email sender configuration is missing in main_backend/.env")

    message = EmailMessage()
    message["Subject"] = f"InsureFlow Policy Issued - {policy_number}"
    message["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_ADDRESS}>"
    message["To"] = recipient_email
    body_lines = [
        "Your InsureFlow policy has been issued successfully.",
        "",
        f"Policy Number: {policy_number}",
        f"Company: {company_name}",
        f"Plan: {plan_name}",
    ]
    if pdf_url:
        body_lines.extend(["", f"Policy PDF: {pdf_url}"])
    body_lines.extend(
        [
            "",
            "Thank you for choosing InsureFlow.",
        ]
    )
    message.set_content("\n".join(body_lines))

    if pdf_file_path:
        attachment_path = Path(pdf_file_path)
        if attachment_path.exists():
            message.add_attachment(
                attachment_path.read_bytes(),
                maintype="application",
                subtype="pdf",
                filename=attachment_path.name,
            )

    try:
        logging.info("Sending policy email to %s for policy %s", recipient_email, policy_number)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(message)
        logging.info("Policy email sent successfully to %s", recipient_email)
    except Exception as error:
        logging.error("Failed to send policy email to %s: %s", recipient_email, error)
        raise

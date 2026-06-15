"""Payment flow tools for the InsureFlow MCP server.

Covers the full mock payment cycle:
- create_payment      : Initiate a payment session for a confirmed offer
- send_payment_otp    : Send a mock payment OTP to the customer's mobile
- verify_payment_otp  : Verify the OTP to complete payment and trigger policy issuance
- get_payment_status  : Check the current status of a payment
"""

from __future__ import annotations

import httpx

from config import MAIN_BACKEND_URL


async def create_payment(
    transaction_id: str,
    user_id: str,
    amount: float,
) -> dict:
    """Create a payment session after the customer confirms their offer.

    This call moves the transaction to PAYMENT_PENDING and generates a
    payment_reference and a mock gateway_url.

    Args:
        transaction_id: The transaction identifier for the current journey.
        user_id: The user identifier returned from the form submission step.
        amount: The final total premium amount to charge (from the selected
                quote item's total_premium field).

    Returns:
        dict containing message, transaction_id, payment_reference,
        payment_status, amount, gateway_url, and created_at.

    Raises:
        Exception: If the backend returns an error or is unreachable.
    """

    payload = {
        "transaction_id": transaction_id,
        "user_id": user_id,
        "amount": amount,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MAIN_BACKEND_URL}/v1/payments",
            json=payload,
            timeout=30.0,
        )

    if response.status_code not in (200, 201):
        raise Exception(
            f"Failed to create payment for transaction {transaction_id}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()


async def send_payment_otp(payment_reference: str) -> dict:
    """Send a mock payment OTP to the customer's registered mobile number.

    The OTP is mock — it is simulated for development and is not a real
    SMS. The customer will use this OTP on the mock payment gateway page.

    Args:
        payment_reference: The payment reference returned by create_payment.

    Returns:
        dict containing message, payment_reference, and otp_expires_at.

    Raises:
        Exception: If the backend returns an error or is unreachable.
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MAIN_BACKEND_URL}/v1/payments/{payment_reference}/send-otp",
            timeout=30.0,
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to send payment OTP for reference {payment_reference}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()


async def verify_payment_otp(
    transaction_id: str,
    payment_reference: str,
    otp: str,
) -> dict:
    """Verify the mock payment OTP to complete the payment.

    A successful verification marks the payment as completed, advances
    the transaction to PURCHASED, and triggers automatic policy issuance
    and PDF generation on the backend.

    Args:
        transaction_id: The transaction identifier for the current journey.
        payment_reference: The payment reference returned by create_payment.
        otp: The OTP value entered by the customer (4 to 8 characters).
             This is a mock OTP for development.

    Returns:
        dict containing message, transaction_id, payment_reference,
        payment_status, verified_at, and policy_number (the issued
        policy number to use for fetching the policy document).

    Raises:
        Exception: If OTP verification fails or the backend is unreachable.
    """

    payload = {
        "transaction_id": transaction_id,
        "payment_reference": payment_reference,
        "otp": otp,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MAIN_BACKEND_URL}/v1/payments/verify-otp",
            json=payload,
            timeout=30.0,
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to verify payment OTP for transaction {transaction_id}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()


async def get_payment_status(payment_reference: str) -> dict:
    """Check the current status of a payment by its reference.

    Useful for polling after OTP verification to confirm the payment
    outcome before fetching the policy.

    Args:
        payment_reference: The payment reference to check.

    Returns:
        dict containing transaction_id, payment_reference, payment_status,
        amount, gateway_url, and updated_at.

    Raises:
        Exception: If the backend returns an error or is unreachable.
    """

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAIN_BACKEND_URL}/v1/payments/{payment_reference}/status",
            timeout=30.0,
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch payment status for reference {payment_reference}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()

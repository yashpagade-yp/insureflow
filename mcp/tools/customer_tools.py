"""Returning customer tools for the InsureFlow MCP server.

Covers the login and resume flow for customers who return after leaving
a journey incomplete or who want to view their purchased policies.

- send_login_otp              : Send a mock OTP to the customer's mobile
- verify_login_otp            : Verify the mock OTP and get a JWT token
- get_user_transactions       : View all transactions for the logged-in customer
- get_latest_incomplete_journey: Find and resume the latest incomplete journey
"""

from __future__ import annotations

import httpx

from config import MAIN_BACKEND_URL


async def send_login_otp(mobile_number: str) -> dict:
    """Send a mock login OTP to a returning customer's mobile number.

    This is a MOCK OTP — no real SMS is sent. The OTP is simulated
    for development purposes. Use the mock OTP value to call
    verify_login_otp to complete authentication.

    Args:
        mobile_number: The customer's registered mobile number
                       (minimum 10 digits).

    Returns:
        dict containing message, mobile_number, and otp_expires_at.

    Raises:
        Exception: If the backend returns an error or is unreachable.
    """

    payload = {"mobile_number": mobile_number}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MAIN_BACKEND_URL}/v1/users/login-otp",
            json=payload,
            timeout=30.0,
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to send login OTP to {mobile_number}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()


async def verify_login_otp(mobile_number: str, otp: str) -> dict:
    """Verify the mock login OTP and get a customer JWT access token.

    After calling send_login_otp, the customer enters the mock OTP.
    A successful verification returns a JWT token which is required
    for viewing policies, transactions, and resuming journeys.

    Args:
        mobile_number: The customer's registered mobile number.
        otp: The mock OTP value received (sent to mobile, simulated).

    Returns:
        dict containing message, access_token, token_type, user_id,
        and mobile_number. Store the access_token for subsequent calls.

    Raises:
        Exception: If OTP verification fails or the backend is unreachable.
    """

    payload = {
        "mobile_number": mobile_number,
        "otp": otp,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MAIN_BACKEND_URL}/v1/users/login-otp/verify",
            json=payload,
            timeout=30.0,
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to verify login OTP for {mobile_number}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()


async def get_user_transactions(user_id: str, token: str) -> dict:
    """Fetch all transactions created by a returning customer.

    Returns all insurance journeys (complete and incomplete) linked to
    the given user. Use this to show the customer their full history
    and find transactions they may want to resume.

    Args:
        user_id: The user identifier returned by verify_login_otp.
        token: The customer JWT token returned by verify_login_otp.

    Returns:
        dict containing a list of transaction records. Each transaction
        includes transaction_id, current_status, created_at, and
        other journey details.

    Raises:
        Exception: If the backend returns an error or is unreachable.
    """

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAIN_BACKEND_URL}/v1/users/{user_id}/transactions",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch transactions for user {user_id}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()


async def get_latest_incomplete_journey(mobile_number: str, token: str) -> dict:
    """Find the latest incomplete insurance journey for a returning customer.

    When a customer left a journey midway (e.g. after quote selection but
    before payment), this tool fetches exactly where they stopped so they
    can resume from that point without starting over.

    Args:
        mobile_number: The customer's registered mobile number.
        token: The customer JWT token returned by verify_login_otp.

    Returns:
        dict containing user_id, transaction_id, current_status, form_step,
        insurance_type, last_active_at, and insurance_detail_id.
        Use transaction_id and current_status to determine which step
        to resume from.

    Raises:
        Exception: If no incomplete journey exists or the backend is unreachable.
    """

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAIN_BACKEND_URL}/v1/users/{mobile_number}/latest-incomplete-journey",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch latest incomplete journey for {mobile_number}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()

"""Policy retrieval tools for the InsureFlow MCP server.

Covers:
- get_policy         : Fetch one issued policy by its policy number
- list_user_policies : List all issued policies for a user (requires customer JWT)
"""

from __future__ import annotations

import httpx

from config import MAIN_BACKEND_URL


async def get_policy(policy_number: str, token: str) -> dict:
    """Fetch one issued insurance policy by its policy number.

    The policy is issued automatically after successful payment OTP
    verification. The policy_number is returned in the verify_payment_otp
    response under the policy_number field.

    Args:
        policy_number: The business-facing policy number (e.g. POL-XXXX-XXXX).
                       This is returned by verify_payment_otp on success.
        token: The customer JWT token obtained after login OTP verification.

    Returns:
        dict containing policy_number, transaction_id, user_id, company_name,
        plan_name, coverage_amount, base_premium, add_ons, add_on_total,
        tax_amount, total_premium, start_date, end_date, payment_reference,
        pdf_url, policy_status, issued_at, and created_at.

    Raises:
        Exception: If the backend returns an error or is unreachable.
    """

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAIN_BACKEND_URL}/v1/policies/{policy_number}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch policy {policy_number}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()


async def list_user_policies(user_id: str, token: str) -> dict:
    """List all issued policies for a customer.

    Requires the customer to be logged in. Returns all policies linked
    to the given user_id, including both active and historical policies.

    Args:
        user_id: The user identifier obtained after login OTP verification.
        token: The customer JWT token obtained after login OTP verification.

    Returns:
        dict containing items (list of policy records) and total_count.

    Raises:
        Exception: If the backend returns an error or is unreachable.
    """

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MAIN_BACKEND_URL}/v1/users/{user_id}/policies",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to list policies for user {user_id}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()

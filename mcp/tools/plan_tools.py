"""Plan and add-on selection tools for the InsureFlow MCP server.

Covers:
- select_plan     : Customer selects one insurance plan from the quotes
- select_add_ons  : Customer selects optional add-ons for the chosen plan
"""

from __future__ import annotations

import httpx

from config import MAIN_BACKEND_URL


async def select_plan(
    transaction_id: str,
    selected_plan_id: str,
) -> dict:
    """Save the customer's selected insurance plan on the transaction.

    After viewing quotes, the customer picks one plan. This call records
    that selection and advances the transaction status to OFFER_SELECTED.

    Args:
        transaction_id: The transaction identifier for the current journey.
        selected_plan_id: The provider plan identifier chosen by the customer.
                          This value comes from the plan_id field in the
                          quote items returned by get_quotes.

    Returns:
        dict containing the updated transaction details including the new
        current_status (OFFER_SELECTED).

    Raises:
        Exception: If the backend returns an error or is unreachable.
    """

    payload = {
        "transaction_id": transaction_id,
        "selected_plan_id": selected_plan_id,
    }

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{MAIN_BACKEND_URL}/v1/transactions/select-plan",
            json=payload,
            timeout=30.0,
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to select plan for transaction {transaction_id}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()


async def select_add_ons(
    transaction_id: str,
    selected_plan_id: str,
    selected_add_ons: list[dict],
) -> dict:
    """Save the customer's selected add-ons for their chosen plan.

    After selecting a plan, the customer can optionally pick add-ons.
    This call records the selected add-ons and advances the transaction
    status to ADD_ONS_SELECTED.

    To skip add-ons, pass an empty list for selected_add_ons.

    Args:
        transaction_id: The transaction identifier for the current journey.
        selected_plan_id: The provider plan identifier already chosen.
        selected_add_ons: List of selected add-on objects. Each object must
                          have 'name' (str) and 'price' (float) fields.
                          Example: [{"name": "Critical Illness", "price": 500.0}]
                          Pass an empty list [] to skip add-ons.

    Returns:
        dict containing the updated transaction details including the new
        current_status (ADD_ONS_SELECTED).

    Raises:
        Exception: If the backend returns an error or is unreachable.
    """

    payload = {
        "transaction_id": transaction_id,
        "selected_plan_id": selected_plan_id,
        "selected_add_ons": selected_add_ons,
    }

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{MAIN_BACKEND_URL}/v1/transactions/select-add-ons",
            json=payload,
            timeout=30.0,
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to save add-ons for transaction {transaction_id}. "
            f"Status: {response.status_code}. Detail: {response.text}"
        )

    return response.json()

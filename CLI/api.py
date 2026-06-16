"""API client for the InsureFlow CLI.

The CLI mirrors the current MCP tool flow but talks directly to the
main backend over HTTP.
"""

from __future__ import annotations

import httpx

from config import MAIN_BACKEND_URL, TIMEOUT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _headers(token: str | None = None) -> dict:
    """Build request headers, optionally with a Bearer token."""
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _post(path: str, payload: dict, token: str | None = None) -> dict:
    """HTTP POST helper. Returns parsed JSON or raises on error."""
    url = f"{MAIN_BACKEND_URL}{path}"
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(url, json=payload, headers=_headers(token))
        resp.raise_for_status()
        return resp.json()


def _patch(path: str, payload: dict, token: str | None = None) -> dict:
    """HTTP PATCH helper."""
    url = f"{MAIN_BACKEND_URL}{path}"
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.patch(url, json=payload, headers=_headers(token))
        resp.raise_for_status()
        return resp.json()


def _get(path: str, token: str | None = None) -> dict:
    """HTTP GET helper."""
    url = f"{MAIN_BACKEND_URL}{path}"
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(url, headers=_headers(token))
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# 1. Insurance Form (No auth required)
# ---------------------------------------------------------------------------

def submit_insurance_form(
    mobile_number: str,
    insurance_type: str,
    first_name: str,
    last_name: str,
    email: str | None = None,
    dob: str | None = None,
    gender: str | None = None,
    sum_insured: float | None = None,
    policy_term_years: int | None = None,
    city: str | None = None,
    state: str | None = None,
) -> dict:
    """Submit the insurance form and start a new journey.

    Returns a dict containing at least: transaction_id, user_id.
    """
    payload: dict = {
        "mobile_number": mobile_number,
        "insurance_type": insurance_type,
        "proposer_first_name": first_name,
        "proposer_last_name": last_name,
        "is_form_completed": True,
    }
    if email:
        payload["proposer_email"] = email
    if dob:
        payload["proposer_dob"] = dob
    if gender:
        payload["proposer_gender"] = gender
    if sum_insured is not None:
        payload["sum_insured_requested"] = sum_insured
    if policy_term_years is not None:
        payload["policy_term_years"] = policy_term_years
    if city:
        payload["city"] = city
    if state:
        payload["state"] = state

    return _post("/v1/insurance-details", payload)


# ---------------------------------------------------------------------------
# 2. Customer Login OTP (No auth required)
# ---------------------------------------------------------------------------

def send_login_otp(mobile_number: str) -> dict:
    """Send a mock login OTP to the customer's mobile."""
    return _post("/v1/users/login-otp", {"mobile_number": mobile_number})


def verify_login_otp(mobile_number: str, otp: str) -> dict:
    """Verify the login OTP. Returns token + user details."""
    return _post(
        "/v1/users/login-otp/verify",
        {"mobile_number": mobile_number, "otp": otp},
    )


# ---------------------------------------------------------------------------
# 3. Quotes (No auth required)
# ---------------------------------------------------------------------------

def get_quotes(transaction_id: str) -> dict:
    """Fetch provider-generated quotes for the transaction."""
    return _get(f"/v1/quotes/{transaction_id}")


# ---------------------------------------------------------------------------
# 4. Plan & Add-on Selection (No auth required)
# ---------------------------------------------------------------------------

def select_plan(transaction_id: str, plan_id: str) -> dict:
    """Save the customer's selected plan on the transaction."""
    return _patch(
        "/v1/transactions/select-plan",
        {"transaction_id": transaction_id, "selected_plan_id": plan_id},
    )


def select_add_ons(
    transaction_id: str,
    plan_id: str,
    add_ons: list[dict],
) -> dict:
    """Save the selected add-ons for the chosen plan."""
    return _patch(
        "/v1/transactions/select-add-ons",
        {
            "transaction_id": transaction_id,
            "selected_plan_id": plan_id,
            "selected_add_ons": add_ons,
        },
    )


# ---------------------------------------------------------------------------
# 5. Payment (Creation + OTP verification require no auth)
# ---------------------------------------------------------------------------

def create_payment(
    transaction_id: str,
    user_id: str,
    amount: float,
) -> dict:
    """Create a payment session for the transaction."""
    return _post(
        "/v1/payments",
        {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "amount": amount,
        },
    )


def send_payment_otp(payment_reference: str) -> dict:
    """Trigger a mock payment OTP for the given payment reference."""
    return _post(f"/v1/payments/{payment_reference}/send-otp", {})


def verify_payment_otp(
    transaction_id: str,
    payment_reference: str,
    otp: str,
) -> dict:
    """Verify the payment OTP. On success the policy is issued."""
    return _post(
        "/v1/payments/verify-otp",
        {
            "transaction_id": transaction_id,
            "payment_reference": payment_reference,
            "otp": otp,
        },
    )


def get_payment_status(payment_reference: str, token: str) -> dict:
    """Fetch payment status for a payment reference."""
    return _get(f"/v1/payments/{payment_reference}/status", token=token)


# ---------------------------------------------------------------------------
# 6. Policies (Requires JWT token)
# ---------------------------------------------------------------------------

def list_user_policies(user_id: str, token: str) -> dict:
    """Fetch all issued policies for the customer."""
    return _get(f"/v1/users/{user_id}/policies", token=token)


def get_policy(policy_number: str, token: str) -> dict:
    """Fetch a single policy by its policy number."""
    return _get(f"/v1/policies/{policy_number}", token=token)


# ---------------------------------------------------------------------------
# 7. Transactions & Resume (Requires JWT token)
# ---------------------------------------------------------------------------

def list_user_transactions(user_id: str, token: str) -> dict:
    """Fetch all transactions for the customer."""
    return _get(f"/v1/users/{user_id}/transactions", token=token)


def get_transaction(transaction_id: str, token: str) -> dict:
    """Fetch a single transaction by transaction_id (status, plan, etc.)."""
    return _get(f"/v1/transactions/{transaction_id}", token=token)


def get_latest_incomplete_journey(mobile_number: str, token: str) -> dict:
    """Fetch the latest incomplete journey for the customer."""
    return _get(
        f"/v1/users/{mobile_number}/latest-incomplete-journey",
        token=token,
    )

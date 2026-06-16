"""InsureFlow MCP Server — entry point.

Transport : Streamable HTTP
Host      : 0.0.0.0 (accessible remotely)
Port      : 8080

This server exposes every step of the InsureFlow customer journey as
an MCP tool so that any MCP-compatible AI client (e.g. Claude Desktop,
Cursor) can drive the full insurance purchase flow end-to-end.

Customer journey tools (in order):
  1. submit_insurance_form        - Fill form, create transaction, get quotes
  2. get_quotes                   - View provider-generated insurance quotes
  3. select_plan                  - Pick one insurance plan
  4. select_add_ons               - Pick optional add-ons for the plan
  5. create_payment               - Initiate payment (PAYMENT_PENDING)
  6. send_payment_otp             - Send mock payment OTP to mobile
  7. verify_payment_otp           - Verify OTP → payment done → policy issued
  8. get_payment_status           - Check payment status by reference
  9. get_policy                   - View the issued policy document

Returning customer tools:
  10. send_login_otp              - Send mock login OTP to mobile
  11. verify_login_otp            - Verify OTP → get JWT token
  12. get_user_transactions       - View all past transactions
  13. get_latest_incomplete_journey - Find and resume an incomplete journey
  14. list_user_policies          - View all purchased policies
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from config import MCP_HOST, MCP_PORT
from tools.insurance_tools import get_quotes, submit_insurance_form
from tools.plan_tools import select_add_ons, select_plan
from tools.payment_tools import (
    create_payment,
    get_payment_status,
    send_payment_otp,
    verify_payment_otp,
)
from tools.policy_tools import get_policy, list_user_policies
from tools.customer_tools import (
    get_latest_incomplete_journey,
    get_user_transactions,
    send_login_otp,
    verify_login_otp,
)
from tools.prompt_tools import (
    new_insurance_journey_prompt,
    returning_customer_prompt,
    resume_incomplete_journey_prompt,
)

# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="insureflow",
    host=MCP_HOST,
    port=MCP_PORT,
    instructions=(
        "You are an InsureFlow assistant. You help customers complete their "
        "insurance purchase journey step by step. "
        "\n\n"
        "NEW CUSTOMER JOURNEY (in order):\n"
        "1. submit_insurance_form  — Fill the form, creates transaction + quotes\n"
        "2. get_quotes             — View available insurance plans and pricing\n"
        "3. select_plan            — Customer picks one plan\n"
        "4. select_add_ons         — Customer picks add-ons (or passes empty list)\n"
        "5. create_payment         — Initiate payment with the total premium\n"
        "6. send_payment_otp       — Send mock OTP to customer's mobile\n"
        "7. verify_payment_otp     — Customer enters OTP → policy is issued\n"
        "8. get_policy             — View the issued policy document\n"
        "\n"
        "RETURNING CUSTOMER FLOW:\n"
        "9.  send_login_otp               — Send mock login OTP\n"
        "10. verify_login_otp             — Verify OTP, get JWT token\n"
        "11. get_user_transactions        — View all past transactions\n"
        "12. get_latest_incomplete_journey — Find where they left off\n"
        "13. list_user_policies           — View all purchased policies\n"
        "\n"
        "Always follow the journey order for new customers. For returning "
        "customers, log them in first before accessing protected tools."
    ),
)


# ---------------------------------------------------------------------------
# Customer journey tools — new purchase flow
# ---------------------------------------------------------------------------


@mcp.tool()
async def tool_submit_insurance_form(
    mobile_number: str,
    insurance_type: str,
    proposer_first_name: str,
    proposer_last_name: str,
    sum_insured_requested: float,
    policy_term_years: int,
    proposer_dob: str = None,
    proposer_email: str = None,
    proposer_gender: str = None,
    occupation: str = None,
    annual_income: float = None,
    city: str = None,
    state: str = None,
    postal_code: str = None,
) -> dict:
    """Submit the insurance details form to start a new customer journey.

    No login or authentication required. The backend automatically
    creates a user from the mobile number, generates a transaction ID,
    and triggers quote generation from the provider backend.

    Use the returned user_id and transaction_id for all subsequent steps.

    insurance_type must be one of the valid InsureFlow insurance categories
    (e.g. HEALTH, LIFE, MOTOR, TRAVEL).

    proposer_dob format: YYYY-MM-DD (e.g. 1990-05-15)
    """

    return await submit_insurance_form(
        mobile_number=mobile_number,
        insurance_type=insurance_type,
        proposer_first_name=proposer_first_name,
        proposer_last_name=proposer_last_name,
        sum_insured_requested=sum_insured_requested,
        policy_term_years=policy_term_years,
        proposer_dob=proposer_dob,
        proposer_email=proposer_email,
        proposer_gender=proposer_gender,
        occupation=occupation,
        annual_income=annual_income,
        city=city,
        state=state,
        postal_code=postal_code,
    )


@mcp.tool()
async def tool_get_quotes(transaction_id: str) -> dict:
    """Retrieve all insurance quotes generated for a transaction.

    Quotes are generated automatically when the insurance form is submitted.
    Each quote item contains plan_id, company_name, plan_name,
    coverage_amount, base_premium, available_add_ons, and total_premium.

    Use plan_id from the desired quote item as selected_plan_id in
    the next step (select_plan).
    """

    return await get_quotes(transaction_id=transaction_id)


@mcp.tool()
async def tool_select_plan(
    transaction_id: str,
    selected_plan_id: str,
) -> dict:
    """Save the customer's selected insurance plan on the transaction.

    selected_plan_id comes from the plan_id field in the quote items
    returned by get_quotes. After this step the transaction status
    moves to OFFER_SELECTED.
    """

    return await select_plan(
        transaction_id=transaction_id,
        selected_plan_id=selected_plan_id,
    )


@mcp.tool()
async def tool_select_add_ons(
    transaction_id: str,
    selected_plan_id: str,
    selected_add_ons: list,
) -> dict:
    """Save the customer's selected add-ons for their chosen plan.

    selected_add_ons is a list of objects, each with 'name' (str) and
    'price' (float). Pass an empty list [] to skip add-ons.

    Example: [{"name": "Critical Illness Cover", "price": 500.0}]

    After this step the transaction status moves to ADD_ONS_SELECTED.
    """

    return await select_add_ons(
        transaction_id=transaction_id,
        selected_plan_id=selected_plan_id,
        selected_add_ons=selected_add_ons,
    )


@mcp.tool()
async def tool_create_payment(
    transaction_id: str,
    user_id: str,
    amount: float,
) -> dict:
    """Create a payment session after the customer confirms their plan and add-ons.

    amount should be the total_premium from the selected quote item.
    Returns a payment_reference and a mock gateway_url.
    Transaction status moves to PAYMENT_PENDING.

    Use the returned payment_reference in the next two steps.
    """

    return await create_payment(
        transaction_id=transaction_id,
        user_id=user_id,
        amount=amount,
    )


@mcp.tool()
async def tool_send_payment_otp(payment_reference: str) -> dict:
    """Send a mock payment OTP to the customer's registered mobile number.

    The OTP is simulated (mock) — no real SMS is sent. The customer
    will use this OTP to verify and complete their payment.

    payment_reference is returned by the create_payment step.
    """

    return await send_payment_otp(payment_reference=payment_reference)


@mcp.tool()
async def tool_verify_payment_otp(
    transaction_id: str,
    payment_reference: str,
    otp: str,
) -> dict:
    """Verify the mock payment OTP to complete the purchase.

    On success: payment is marked complete, transaction moves to PURCHASED,
    and a policy is automatically issued. The returned policy_number can
    be used to fetch the policy document with get_policy.

    otp is the mock OTP value the customer received after send_payment_otp.
    """

    return await verify_payment_otp(
        transaction_id=transaction_id,
        payment_reference=payment_reference,
        otp=otp,
    )


@mcp.tool()
async def tool_get_payment_status(payment_reference: str, token: str) -> dict:
    """Check the current status of a payment by its reference.

    Requires the customer JWT token (from verify_login_otp) because the
    backend restricts this endpoint to the payment owner or an admin.

    Useful for confirming whether payment succeeded or failed before
    attempting to fetch the policy.
    """

    return await get_payment_status(payment_reference=payment_reference, token=token)


@mcp.tool()
async def tool_get_policy(policy_number: str, token: str) -> dict:
    """Fetch the issued insurance policy document by its policy number.

    policy_number is returned in the verify_payment_otp response.
    token is the customer JWT obtained after login OTP verification.

    Returns full policy details including company_name, plan_name,
    coverage_amount, total_premium, start_date, end_date, and pdf_url.
    """

    return await get_policy(policy_number=policy_number, token=token)


# ---------------------------------------------------------------------------
# Returning customer tools — login and resume flow
# ---------------------------------------------------------------------------


@mcp.tool()
async def tool_send_login_otp(mobile_number: str) -> dict:
    """Send a mock login OTP to a returning customer's mobile number.

    Use this when a customer wants to log back in to view their policy
    or resume an incomplete journey. The OTP is mock (simulated).

    After calling this, use verify_login_otp with the mock OTP to
    get a JWT access token.
    """

    return await send_login_otp(mobile_number=mobile_number)


@mcp.tool()
async def tool_verify_login_otp(mobile_number: str, otp: str) -> dict:
    """Verify the mock login OTP and get a customer JWT access token.

    Returns access_token and user_id. Store both — access_token is
    required for all protected returning-customer tools (get_policy,
    get_user_transactions, get_latest_incomplete_journey, list_user_policies).
    """

    return await verify_login_otp(mobile_number=mobile_number, otp=otp)


@mcp.tool()
async def tool_get_user_transactions(user_id: str, token: str) -> dict:
    """Fetch all insurance transactions for a returning logged-in customer.

    Returns all journeys (complete and incomplete) linked to the user.
    Use current_status to identify which transactions are complete
    (PURCHASED) and which are still in progress.
    """

    return await get_user_transactions(user_id=user_id, token=token)


@mcp.tool()
async def tool_get_latest_incomplete_journey(
    mobile_number: str,
    token: str,
) -> dict:
    """Find the latest incomplete insurance journey for a returning customer.

    Returns the transaction_id and current_status of the most recent
    incomplete journey. Use current_status to determine which step to
    resume from in the customer journey flow.
    """

    return await get_latest_incomplete_journey(
        mobile_number=mobile_number,
        token=token,
    )


@mcp.tool()
async def tool_list_user_policies(user_id: str, token: str) -> dict:
    """List all issued insurance policies for a logged-in customer.

    Returns all purchased policies with full details including
    policy_number, plan_name, coverage_amount, total_premium,
    start_date, end_date, and pdf_url for each policy.
    """

    return await list_user_policies(user_id=user_id, token=token)


# ---------------------------------------------------------------------------
# Prompts — conversation starters for MCP-compatible clients
# ---------------------------------------------------------------------------


@mcp.prompt()
def prompt_new_insurance_journey() -> str:
    """Start a new insurance purchase journey from scratch.

    Guides the AI to collect customer details, submit the form,
    display quotes, select a plan and add-ons, process payment,
    and retrieve the issued policy — end to end.
    """

    return new_insurance_journey_prompt()


@mcp.prompt()
def prompt_returning_customer() -> str:
    """Log in a returning customer and help them with their account.

    Guides the AI to authenticate the customer via OTP and then
    let them view their policies, view past transactions, or
    resume an incomplete insurance purchase.
    """

    return returning_customer_prompt()


@mcp.prompt()
def prompt_resume_incomplete_journey() -> str:
    """Resume an insurance purchase that was left incomplete.

    Guides the AI to log in the customer, find their latest
    incomplete journey, and resume from exactly where they left off
    without starting the entire process over again.
    """

    return resume_incomplete_journey_prompt()


# ---------------------------------------------------------------------------
# Run server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable-http")

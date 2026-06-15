"""InsureFlow CLI - Interactive Customer Journey.

Run with:
    python main.py

Flows:
    1. New Customer  -> fill form -> OTP login -> quotes -> plan -> payment -> policy
    2. Returning Customer -> OTP login -> view policies / transactions / resume journey
"""

from __future__ import annotations

import sys

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

import api

console = Console()


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def print_header() -> None:
    """Print the InsureFlow welcome banner."""
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]  InsureFlow  [/bold cyan]\n"
            "[dim]Your Smart Insurance Assistant[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    console.print()


def print_step(number: int, title: str) -> None:
    """Print a styled step header."""
    console.print(f"\n[bold yellow]-- Step {number}: {title} --[/bold yellow]")


def print_success(message: str) -> None:
    console.print(f"\n[bold green]OK  {message}[/bold green]")


def print_error(message: str) -> None:
    console.print(f"\n[bold red]ERR {message}[/bold red]")


def print_info(message: str) -> None:
    console.print(f"[dim cyan]... {message}[/dim cyan]")


def ask(prompt: str, default: str = "") -> str:
    """Prompt the user and return stripped input."""
    return Prompt.ask(f"[bold white]{prompt}[/bold white]", default=default).strip()


def ask_int(prompt: str, default: int = 1) -> int | None:
    """Prompt for an integer; return None on invalid input."""
    raw = ask(prompt, default=str(default))
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        print_error("Please enter a valid number.")
        return ask_int(prompt, default)


def ask_float(prompt: str) -> float | None:
    """Prompt for a float; return None if blank."""
    raw = ask(prompt, default="")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        print_error("Please enter a valid amount.")
        return ask_float(prompt)


def safe_call(fn, *args, action: str = "Calling API", **kwargs):
    """Wrap an API call with a spinner. Returns result or None on error."""
    with console.status(f"[cyan]{action}...[/cyan]"):
        try:
            return fn(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", str(e))
            except Exception:
                detail = str(e)
            print_error(f"API Error: {detail}")
            return None
        except httpx.ConnectError:
            print_error(
                "Cannot connect to backend. "
                "Make sure main_backend is running on http://localhost:8000"
            )
            return None
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            return None


# ---------------------------------------------------------------------------
# OTP Login Helper
# ---------------------------------------------------------------------------

def do_login(mobile_number: str) -> tuple[str, str] | None:
    """Send OTP and verify. Returns (token, user_id) or None."""
    print_info(f"Sending OTP to mobile: {mobile_number}")
    result = safe_call(api.send_login_otp, mobile_number, action="Sending OTP")
    if not result:
        return None

    print_success("OTP sent! (Mock OTP - check backend logs for the code)")
    otp = ask("Enter OTP")

    verify = safe_call(api.verify_login_otp, mobile_number, otp, action="Verifying OTP")
    if not verify:
        return None

    token = verify.get("access_token") or verify.get("token")
    user_id = verify.get("user_id") or verify.get("id")

    if not token:
        print_error("Login failed - no token received.")
        return None

    print_success("Login successful!")
    return token, user_id


# ---------------------------------------------------------------------------
# Display Helpers
# ---------------------------------------------------------------------------

def display_quotes_table(quotes: list[dict]) -> None:
    """Render a Rich table of insurance quotes."""
    table = Table(
        title="[bold cyan]Available Insurance Quotes[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
        padding=(0, 1),
    )
    table.add_column("#", style="bold white", justify="center", width=4)
    table.add_column("Company", style="bold cyan")
    table.add_column("Plan", style="yellow")
    table.add_column("Plan ID", style="dim", overflow="fold")
    table.add_column("Coverage", style="green", justify="right")
    table.add_column("Base Premium", style="bold green", justify="right")
    table.add_column("Term", justify="center")
    table.add_column("Add-ons", justify="center")

    for i, q in enumerate(quotes, start=1):
        add_ons = q.get("add_ons") or q.get("available_add_ons") or []
        table.add_row(
            str(i),
            str(q.get("company_name", "-")),
            str(q.get("plan_name", "-")),
            str(q.get("plan_id", q.get("selected_plan_id", "-"))),
            f"Rs.{q.get('coverage_amount', q.get('sum_insured', 0)):,.0f}",
            f"Rs.{q.get('base_premium', q.get('premium', 0)):,.0f}",
            f"{q.get('duration_years', q.get('policy_term_years', '-'))} yr",
            str(len(add_ons)),
        )
    console.print()
    console.print(table)


def display_add_ons_table(add_ons: list[dict]) -> None:
    """Render a Rich table of add-ons."""
    if not add_ons:
        print_info("No add-ons available for this plan.")
        return
    table = Table(
        title="[bold yellow]Available Add-ons[/bold yellow]",
        box=box.SIMPLE_HEAVY,
        border_style="yellow",
        padding=(0, 1),
    )
    table.add_column("#", style="bold white", justify="center", width=4)
    table.add_column("Add-on Name", style="yellow")
    table.add_column("Price", style="green", justify="right")
    for i, ao in enumerate(add_ons, start=1):
        table.add_row(str(i), str(ao.get("name", "-")), f"Rs.{ao.get('price', 0):,.0f}")
    console.print()
    console.print(table)


def display_policy(policy: dict) -> None:
    """Render a full policy summary panel with PDF link."""
    lines = [
        f"[bold cyan]Policy Number:[/bold cyan]  {policy.get('policy_number', '-')}",
        f"[bold cyan]Company:[/bold cyan]        {policy.get('company_name', '-')}",
        f"[bold cyan]Plan:[/bold cyan]           {policy.get('plan_name', '-')}",
        f"[bold cyan]Coverage:[/bold cyan]       Rs.{policy.get('coverage_amount', 0):,.0f}",
        f"[bold cyan]Base Premium:[/bold cyan]   Rs.{policy.get('base_premium', 0):,.0f}",
        f"[bold cyan]Total Premium:[/bold cyan]  Rs.{policy.get('total_premium', 0):,.0f}",
        f"[bold cyan]Term:[/bold cyan]           {policy.get('duration_years', '-')} years",
        f"[bold cyan]Status:[/bold cyan]         {policy.get('status', '-')}",
    ]
    pdf = policy.get("pdf_url")
    if pdf:
        lines.append(f"[bold cyan]Policy PDF:[/bold cyan]     {pdf}")
    console.print()
    console.print(
        Panel(
            "\n".join(lines),
            title="[bold green]  Policy Details  [/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


def display_policies_list(policies: list[dict]) -> None:
    """Display all user policies in a table."""
    if not policies:
        print_info("No policies found.")
        return
    table = Table(
        title="[bold cyan]Your Policies[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
        padding=(0, 1),
    )
    table.add_column("#", style="bold white", justify="center", width=4)
    table.add_column("Policy Number", style="bold cyan")
    table.add_column("Company", style="yellow")
    table.add_column("Plan", style="yellow")
    table.add_column("Coverage", style="green", justify="right")
    table.add_column("Premium", style="bold green", justify="right")
    table.add_column("Status", justify="center")
    for i, p in enumerate(policies, start=1):
        status = p.get("status", "-")
        style = "green" if status == "ACTIVE" else "yellow"
        table.add_row(
            str(i),
            str(p.get("policy_number", "-")),
            str(p.get("company_name", "-")),
            str(p.get("plan_name", "-")),
            f"Rs.{p.get('coverage_amount', 0):,.0f}",
            f"Rs.{p.get('total_premium', 0):,.0f}",
            f"[{style}]{status}[/{style}]",
        )
    console.print()
    console.print(table)


def display_transactions_list(transactions: list[dict]) -> None:
    """Display all user transactions in a table."""
    if not transactions:
        print_info("No transactions found.")
        return
    table = Table(
        title="[bold cyan]Your Transactions[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
        padding=(0, 1),
    )
    table.add_column("#", style="bold white", justify="center", width=4)
    table.add_column("Transaction ID", style="dim", overflow="fold")
    table.add_column("Type", style="yellow")
    table.add_column("Status", style="bold")
    table.add_column("Created At")
    for i, t in enumerate(transactions, start=1):
        status = t.get("status", "-")
        style = "green" if status == "PURCHASED" else "yellow"
        table.add_row(
            str(i),
            str(t.get("transaction_id", "-")),
            str(t.get("insurance_type", "-")).upper(),
            f"[{style}]{status}[/{style}]",
            str(t.get("created_at", "-"))[:19],
        )
    console.print()
    console.print(table)


# ---------------------------------------------------------------------------
# New Customer Flow
# ---------------------------------------------------------------------------

def flow_new_customer() -> None:
    """Complete new customer insurance purchase journey.

    Step 1:  Collect form details
    Step 2:  Submit form (no auth) -> transaction_id + user_id created
    Step 3:  OTP login -> get JWT token
    Step 4:  Fetch quotes (requires JWT)
    Step 5:  Select plan
    Step 6:  Select add-ons (optional)
    Step 7:  Create payment session
    Step 8:  Verify payment OTP -> policy auto-issued
    Step 9:  Show issued policy with PDF
    """

    # Step 1: Personal Details
    print_step(1, "Personal Details")

    mobile = ask("Mobile Number (10 digits)")
    if not mobile or len(mobile) < 10:
        print_error("Mobile number must be at least 10 digits.")
        return

    console.print("\n[bold yellow]Insurance Type:[/bold yellow]")
    console.print("  [bold white]1.[/bold white] Health")
    console.print("  [bold white]2.[/bold white] Life")
    console.print("  [bold white]3.[/bold white] General")
    ins_choice = ask("Select insurance type", default="1")
    insurance_type = {"1": "health", "2": "life", "3": "general"}.get(ins_choice, "health")

    first_name = ask("First Name")
    last_name = ask("Last Name")
    email = ask("Email (optional, press Enter to skip)")
    dob = ask("Date of Birth YYYY-MM-DD (optional)")

    console.print("\n[bold yellow]Gender:[/bold yellow]")
    console.print("  [bold white]1.[/bold white] Male")
    console.print("  [bold white]2.[/bold white] Female")
    console.print("  [bold white]3.[/bold white] Other")
    gender = {"1": "male", "2": "female", "3": "other"}.get(ask("Select gender", default="1"), "male")

    sum_insured = ask_float("Sum Insured e.g. 500000 (optional, press Enter to skip)")
    policy_term = ask_int("Policy Term in Years e.g. 1 (optional, press Enter to skip)", default=0) or None
    city = ask("City (optional)")
    state_name = ask("State (optional)")

    # Step 2: Submit Form (NO auth required)
    print_step(2, "Submitting Insurance Form")
    form_result = safe_call(
        api.submit_insurance_form,
        mobile, insurance_type, first_name, last_name,
        email or None, dob or None, gender,
        sum_insured, policy_term, city or None, state_name or None,
        action="Submitting form",
    )
    if not form_result:
        return

    transaction_id = form_result.get("transaction_id")
    user_id = form_result.get("user_id")
    print_success(f"Form submitted! Transaction ID: [bold]{transaction_id}[/bold]")

    # Step 3: OTP Login (customer verifies mobile to get JWT)
    print_step(3, "Verify Your Mobile via OTP")
    login = do_login(mobile)
    if not login:
        return
    token, uid = login
    user_id = uid or user_id

    # Step 4: Fetch Quotes (requires JWT)
    print_step(4, "Fetching Quotes from Providers")
    quotes_resp = safe_call(api.get_quotes, transaction_id, token, action="Fetching quotes")
    if not quotes_resp:
        return

    quotes: list[dict] = (
        quotes_resp.get("quotes") or quotes_resp.get("data")
        or (quotes_resp if isinstance(quotes_resp, list) else [])
    )
    if not quotes:
        print_error("No quotes available for this transaction.")
        return
    display_quotes_table(quotes)

    # Step 5: Select Plan
    print_step(5, "Select a Plan")
    plan_num = ask_int(f"Enter plan number (1-{len(quotes)})", default=1)
    if plan_num is None or not (1 <= plan_num <= len(quotes)):
        print_error("Invalid plan selection.")
        return

    chosen_quote = quotes[plan_num - 1]
    chosen_plan_id = (
        chosen_quote.get("plan_id")
        or chosen_quote.get("selected_plan_id")
        or chosen_quote.get("id")
    )
    chosen_premium = float(chosen_quote.get("base_premium") or chosen_quote.get("premium") or 0)

    safe_call(api.select_plan, transaction_id, chosen_plan_id, token, action="Saving plan selection")
    print_success(f"Plan selected: [bold]{chosen_quote.get('plan_name', chosen_plan_id)}[/bold]")

    # Step 6: Select Add-ons (optional)
    print_step(6, "Select Add-ons (Optional)")
    available_add_ons = chosen_quote.get("add_ons") or chosen_quote.get("available_add_ons") or []
    selected_add_ons: list[dict] = []

    if available_add_ons:
        display_add_ons_table(available_add_ons)
        if Confirm.ask("[bold white]Would you like to add any add-ons?[/bold white]", default=False):
            raw = ask("Enter add-on numbers separated by commas e.g. 1,2 (or Enter to skip)")
            if raw.strip():
                for x in raw.split(","):
                    if x.strip().isdigit():
                        n = int(x.strip())
                        if 1 <= n <= len(available_add_ons):
                            ao = available_add_ons[n - 1]
                            selected_add_ons.append({"name": ao.get("name", ""), "price": ao.get("price", 0)})
                            chosen_premium += float(ao.get("price", 0))

    safe_call(
        api.select_add_ons, transaction_id, chosen_plan_id, selected_add_ons, token,
        action="Saving add-on selections",
    )
    if selected_add_ons:
        print_success(f"Add-ons saved: {[ao['name'] for ao in selected_add_ons]}")
    else:
        print_info("No add-ons selected.")

    # Step 7: Create Payment Session
    print_step(7, "Payment")
    console.print(f"\n[bold white]Total Amount Payable:[/bold white] [bold green]Rs.{chosen_premium:,.0f}[/bold green]")

    if not Confirm.ask("[bold white]Proceed with payment?[/bold white]", default=True):
        print_info("Payment cancelled. Your journey is saved - you can resume it later.")
        return

    payment_resp = safe_call(
        api.create_payment, transaction_id, user_id, chosen_premium, token,
        action="Creating payment session",
    )
    if not payment_resp:
        return

    payment_reference = (
        payment_resp.get("payment_reference")
        or payment_resp.get("reference")
        or payment_resp.get("id")
    )
    print_success(f"Payment session created. Reference: [bold]{payment_reference}[/bold]")

    # Step 8: Payment OTP
    print_step(8, "Confirm Payment via OTP")
    safe_call(api.send_payment_otp, payment_reference, token, action="Sending payment OTP")
    print_success("Payment OTP sent! (Mock OTP - check backend logs for the code)")

    pay_otp = ask("Enter Payment OTP")
    verify_resp = safe_call(
        api.verify_payment_otp, transaction_id, payment_reference, pay_otp, token,
        action="Verifying payment OTP",
    )
    if not verify_resp:
        return

    print_success("Payment verified! Policy is being issued...")

    # Step 9: Show Issued Policy
    print_step(9, "Your Policy")
    policies_resp = safe_call(api.list_user_policies, user_id, token, action="Fetching your policy")

    policies: list[dict] = []
    if policies_resp:
        policies = (
            policies_resp.get("policies") or policies_resp.get("data")
            or (policies_resp if isinstance(policies_resp, list) else [])
        )

    if policies:
        display_policy(policies[-1])
    else:
        # Try from verify_resp directly
        policy_number = (
            verify_resp.get("policy_number")
            or (verify_resp.get("policy") or {}).get("policy_number")
        )
        if policy_number:
            pol = safe_call(api.get_policy, policy_number, token, action="Fetching policy")
            if pol:
                display_policy(pol)
        else:
            print_success("Payment complete! Policy has been issued.")
            print_info("Login as Returning Customer to view your policy and PDF.")


# ---------------------------------------------------------------------------
# Returning Customer Flow
# ---------------------------------------------------------------------------

def flow_returning_customer() -> None:
    """Returning customer: OTP login -> view policies / transactions / smart resume.

    The resume journey is SMART - it checks the current transaction status
    and jumps directly to the right step instead of starting from scratch.

    Status routing:
        PURCHASED / COMPLETED    -> Show policy (done)
        PAYMENT_PENDING          -> Go to payment OTP
        ADD_ONS_SELECTED         -> Go to payment
        OFFER_SELECTED           -> Go to add-ons then payment
        FORM_SUBMITTED / UNKNOWN -> Show quotes, select plan, add-ons, payment
    """

    # Login
    print_step(1, "Login")
    mobile = ask("Mobile Number")
    if not mobile:
        return

    login = do_login(mobile)
    if not login:
        return
    token, user_id = login

    console.print("\n[bold yellow]What would you like to do?[/bold yellow]")
    console.print("  [bold white]1.[/bold white] View my issued policies (with PDF)")
    console.print("  [bold white]2.[/bold white] View all my transactions + status + payment")
    console.print("  [bold white]3.[/bold white] Resume my latest incomplete journey")
    choice = ask("Select option", default="1")

    # Option 1: View Policies
    if choice == "1":
        print_step(2, "Your Policies")
        resp = safe_call(api.list_user_policies, user_id, token, action="Fetching policies")
        if not resp:
            return
        policies = (
            resp.get("policies") or resp.get("data")
            or (resp if isinstance(resp, list) else [])
        )
        display_policies_list(policies)
        if policies and Confirm.ask("\n[bold white]View full details of a policy?[/bold white]", default=False):
            num = ask_int(f"Enter policy number (1-{len(policies)})", default=1)
            if num and 1 <= num <= len(policies):
                display_policy(policies[num - 1])

    # Option 2: View Transactions with detail + payment status
    elif choice == "2":
        print_step(2, "Your Transactions")
        resp = safe_call(api.list_user_transactions, user_id, token, action="Fetching transactions")
        if not resp:
            return
        txns = (
            resp.get("transactions") or resp.get("data")
            or (resp if isinstance(resp, list) else [])
        )
        display_transactions_list(txns)
        if not txns:
            return

        if not Confirm.ask("\n[bold white]View details of a specific transaction?[/bold white]", default=False):
            return

        num = ask_int(f"Enter transaction number (1-{len(txns)})", default=1)
        if not num or num < 1 or num > len(txns):
            return

        tid = txns[num - 1].get("transaction_id") or txns[num - 1].get("id")
        detail = safe_call(api.get_transaction, tid, token, action="Fetching transaction details")
        if detail:
            pay_ref = detail.get("payment_reference") or "-"
            console.print()
            console.print(
                Panel(
                    f"[bold cyan]Transaction ID:[/bold cyan]      {tid}\n"
                    f"[bold cyan]Insurance Type:[/bold cyan]      {detail.get('insurance_type', '-').upper()}\n"
                    f"[bold cyan]Status:[/bold cyan]              [yellow]{detail.get('status', '-')}[/yellow]\n"
                    f"[bold cyan]Selected Plan:[/bold cyan]       {detail.get('selected_plan_id', 'Not selected yet')}\n"
                    f"[bold cyan]Payment Reference:[/bold cyan]   {pay_ref}\n"
                    f"[bold cyan]Created At:[/bold cyan]          {str(detail.get('created_at', '-'))[:19]}",
                    title="[bold cyan]  Transaction Detail  [/bold cyan]",
                    border_style="cyan",
                    padding=(1, 2),
                )
            )
            # Check payment status if ref exists
            if pay_ref and pay_ref != "-":
                if Confirm.ask("\n[bold white]Check payment status?[/bold white]", default=False):
                    pay_status = safe_call(
                        api.get_payment_status, pay_ref, token, action="Fetching payment status"
                    )
                    if pay_status:
                        console.print()
                        console.print(
                            Panel(
                                f"[bold cyan]Payment Reference:[/bold cyan]  {pay_ref}\n"
                                f"[bold cyan]Amount:[/bold cyan]             Rs.{pay_status.get('amount', 0):,.0f}\n"
                                f"[bold cyan]Payment Status:[/bold cyan]     [yellow]{pay_status.get('status', '-')}[/yellow]",
                                title="[bold yellow]  Payment Status  [/bold yellow]",
                                border_style="yellow",
                                padding=(1, 2),
                            )
                        )

    # Option 3: Smart Resume
    elif choice == "3":
        print_step(2, "Resume Incomplete Journey")
        resp = safe_call(
            api.get_latest_incomplete_journey, mobile, token,
            action="Fetching incomplete journey",
        )
        if not resp:
            return

        transaction_id = resp.get("transaction_id") or resp.get("id")
        ins_type = resp.get("insurance_type", "-").upper()
        if not transaction_id:
            print_error("No incomplete journey found.")
            return

        # Get full transaction to know exact status
        txn = safe_call(api.get_transaction, transaction_id, token, action="Checking journey status")
        current_status = (txn or {}).get("status", "UNKNOWN")
        pay_ref = (txn or {}).get("payment_reference")
        selected_plan_id = (txn or {}).get("selected_plan_id")
        amount = float((txn or {}).get("total_premium") or (txn or {}).get("amount") or 0)

        console.print()
        console.print(
            Panel(
                f"[bold cyan]Transaction ID:[/bold cyan]  {transaction_id}\n"
                f"[bold cyan]Insurance Type:[/bold cyan]  {ins_type}\n"
                f"[bold cyan]Current Status:[/bold cyan]  [yellow]{current_status}[/yellow]",
                title="[bold yellow]  Incomplete Journey Found  [/bold yellow]",
                border_style="yellow",
                padding=(1, 2),
            )
        )

        if not Confirm.ask("[bold white]Resume this journey?[/bold white]", default=True):
            return

        # Status routing
        STATUS_DONE = {"PURCHASED", "COMPLETED", "POLICY_ISSUED"}
        STATUS_PAYMENT = {"PAYMENT_PENDING", "PAYMENT_CREATED"}
        STATUS_ADDONS = {"ADD_ONS_SELECTED"}
        STATUS_PLAN = {"OFFER_SELECTED", "PLAN_SELECTED"}
        STATUS_FORM = {"FORM_SUBMITTED", "PENDING", "QUOTE_PENDING", "CREATED", "UNKNOWN"}

        # Already done
        if current_status in STATUS_DONE:
            print_success("This journey is already complete!")
            p_resp = safe_call(api.list_user_policies, user_id, token, action="Fetching policy")
            if p_resp:
                pols = (
                    p_resp.get("policies") or p_resp.get("data")
                    or (p_resp if isinstance(p_resp, list) else [])
                )
                if pols:
                    display_policy(pols[-1])
            return

        quotes: list[dict] = []
        chosen_quote: dict | None = None

        # Fetch quotes for any status except payment pending
        if current_status not in STATUS_PAYMENT:
            print_step(3, "Fetching Quotes")
            q_resp = safe_call(api.get_quotes, transaction_id, token, action="Fetching quotes")
            if not q_resp:
                return
            quotes = (
                q_resp.get("quotes") or q_resp.get("data")
                or (q_resp if isinstance(q_resp, list) else [])
            )
            if not quotes:
                print_error("No quotes found.")
                return
            display_quotes_table(quotes)

            # Find already selected plan
            if selected_plan_id:
                for q in quotes:
                    if (q.get("plan_id") or q.get("id")) == selected_plan_id:
                        chosen_quote = q
                        amount = float(q.get("base_premium") or q.get("premium") or 0)
                        break

        # Select plan if needed
        if current_status in STATUS_FORM or not selected_plan_id:
            print_step(4, "Select a Plan")
            plan_num = ask_int(f"Select plan (1-{len(quotes)})", default=1)
            if not plan_num or not (1 <= plan_num <= len(quotes)):
                print_error("Invalid selection.")
                return
            chosen_quote = quotes[plan_num - 1]
            selected_plan_id = (
                chosen_quote.get("plan_id") or chosen_quote.get("selected_plan_id") or chosen_quote.get("id")
            )
            amount = float(chosen_quote.get("base_premium") or chosen_quote.get("premium") or 0)
            safe_call(api.select_plan, transaction_id, selected_plan_id, token, action="Saving plan")
            print_success(f"Plan selected: [bold]{chosen_quote.get('plan_name', selected_plan_id)}[/bold]")
            current_status = "OFFER_SELECTED"

        # Add-ons if at plan stage
        if current_status in STATUS_PLAN | STATUS_FORM:
            available_add_ons = (chosen_quote or {}).get("add_ons") or (chosen_quote or {}).get("available_add_ons") or []
            selected_add_ons: list[dict] = []
            if available_add_ons:
                print_step(5, "Add-ons (Optional)")
                display_add_ons_table(available_add_ons)
                if Confirm.ask("[bold white]Add any add-ons?[/bold white]", default=False):
                    raw = ask("Enter add-on numbers e.g. 1,2 (or Enter to skip)")
                    if raw.strip():
                        for x in raw.split(","):
                            if x.strip().isdigit():
                                n = int(x.strip())
                                if 1 <= n <= len(available_add_ons):
                                    ao = available_add_ons[n - 1]
                                    selected_add_ons.append({"name": ao.get("name", ""), "price": ao.get("price", 0)})
                                    amount += float(ao.get("price", 0))
            safe_call(
                api.select_add_ons, transaction_id, selected_plan_id, selected_add_ons, token,
                action="Saving add-ons",
            )
            current_status = "ADD_ONS_SELECTED"

        # Create payment if not already pending
        if current_status not in STATUS_PAYMENT:
            print_step(6, "Payment")
            console.print(f"\n[bold white]Amount Payable:[/bold white] [bold green]Rs.{amount:,.0f}[/bold green]")
            if not Confirm.ask("[bold white]Proceed with payment?[/bold white]", default=True):
                print_info("Payment cancelled. Journey saved.")
                return
            pay_resp = safe_call(
                api.create_payment, transaction_id, user_id, amount, token,
                action="Creating payment session",
            )
            if not pay_resp:
                return
            pay_ref = (
                pay_resp.get("payment_reference") or pay_resp.get("reference") or pay_resp.get("id")
            )
            print_success(f"Payment created. Reference: [bold]{pay_ref}[/bold]")

        # Payment OTP
        print_step(7, "Confirm Payment via OTP")
        safe_call(api.send_payment_otp, pay_ref, token, action="Sending payment OTP")
        print_success("Payment OTP sent! (Mock OTP - check backend logs for the code)")

        pay_otp = ask("Enter Payment OTP")
        verify_resp = safe_call(
            api.verify_payment_otp, transaction_id, pay_ref, pay_otp, token,
            action="Verifying payment OTP",
        )
        if not verify_resp:
            return

        print_success("Payment verified! Policy issued.")

        print_step(8, "Your Policy")
        p_resp = safe_call(api.list_user_policies, user_id, token, action="Fetching policy")
        if p_resp:
            pols = (
                p_resp.get("policies") or p_resp.get("data")
                or (p_resp if isinstance(p_resp, list) else [])
            )
            if pols:
                display_policy(pols[-1])

    else:
        print_error("Invalid choice.")


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """Main entry point for the InsureFlow CLI."""
    print_header()

    console.print("[bold white]Welcome to InsureFlow![/bold white]")
    console.print("[dim]India's smart, AI-ready insurance platform.[/dim]\n")

    console.print("[bold yellow]Who are you?[/bold yellow]")
    console.print("  [bold white]1.[/bold white] New Customer - Start a new insurance journey")
    console.print("  [bold white]2.[/bold white] Returning Customer - Login to view or resume")
    console.print("  [bold white]0.[/bold white] Exit\n")

    choice = ask("Select option", default="1")

    if choice == "1":
        flow_new_customer()
    elif choice == "2":
        flow_returning_customer()
    elif choice == "0":
        console.print("\n[dim]Goodbye! Stay insured.[/dim]\n")
        sys.exit(0)
    else:
        print_error("Invalid option. Please run again and choose 1 or 2.")
        sys.exit(1)

    console.print()
    console.print(
        Panel(
            "[bold cyan]Thank you for using InsureFlow![/bold cyan]\n"
            "[dim]Your health and safety - always our priority.[/dim]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()


if __name__ == "__main__":
    main()

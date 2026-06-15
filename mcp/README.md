# InsureFlow MCP Server

A **Model Context Protocol (MCP) server** that exposes the complete InsureFlow
customer insurance journey as AI-callable tools. Any MCP-compatible AI client
(e.g. Claude Desktop, Cursor) can drive the entire purchase flow end-to-end
through this server.

---

## What Is MCP?

MCP (Model Context Protocol) is an open standard by Anthropic that lets AI
assistants call external tools and services in a structured way. Instead of
an AI just chatting, it can actually *do things* — like submitting a form,
fetching quotes, or processing a payment — by calling tools exposed by an
MCP server.

---

## Transport

This server uses **Streamable HTTP** transport, meaning it runs as a real
HTTP server that any MCP client can connect to remotely.

| Setting | Value |
|---------|-------|
| Protocol | Streamable HTTP |
| Host | `0.0.0.0` (accessible remotely) |
| Port | `8080` |
| MCP endpoint | `http://localhost:8080/mcp` |

---

## Architecture

```
AI Client (Claude Desktop / Cursor)
        │
        │ MCP Protocol (Streamable HTTP)
        ▼
InsureFlow MCP Server  (port 8080)
        │
        ├──▶ main_backend    (port 8000)   ← Customer journey
        │
        └──▶ provider_backend (port 8001)  ← Quotes / Plans (via main_backend)
```

The MCP server acts as a **middleware** — it receives tool calls from the AI
client and forwards them as REST API calls to the correct backend.

---

## Customer Journey Flow

The entire InsureFlow insurance purchase journey is exposed as MCP tools,
called in this order:

### Phase 1 — Form Submission (No auth required)

```
Customer fills form
        │
        ▼
[Tool] submit_insurance_form
        │
        ├── Creates user (by mobile number)
        ├── Generates transaction_id
        └── Triggers quote generation on provider_backend
        │
        ▼
Returns: user_id + transaction_id
```

### Phase 2 — View Quotes

```
[Tool] get_quotes(transaction_id)
        │
        └── Returns list of plans with pricing, benefits, add-ons
```

### Phase 3 — Select Plan & Add-ons

```
[Tool] select_plan(transaction_id, selected_plan_id)
        │
        └── Transaction status → OFFER_SELECTED

[Tool] select_add_ons(transaction_id, selected_plan_id, selected_add_ons)
        │
        └── Transaction status → ADD_ONS_SELECTED
```

### Phase 4 — Payment (Mock)

```
[Tool] create_payment(transaction_id, user_id, amount)
        │
        └── Returns payment_reference + mock gateway_url
        │   Transaction status → PAYMENT_PENDING

[Tool] send_payment_otp(payment_reference)
        │
        └── Mock OTP sent to customer's mobile (simulated, not real SMS)

[Tool] verify_payment_otp(transaction_id, payment_reference, otp)
        │
        ├── Payment marked COMPLETED
        ├── Transaction status → PURCHASED
        └── Policy automatically issued → Returns policy_number
```

### Phase 5 — Get Policy

```
[Tool] get_policy(policy_number, token)
        │
        └── Returns full policy: company, plan, coverage, premium, PDF URL
```

---

## Returning Customer Flow (Login + Resume / View)

When a customer returns later (to view policy or resume an incomplete journey):

```
[Tool] send_login_otp(mobile_number)
        │
        └── Mock OTP sent (simulated, not real SMS)

[Tool] verify_login_otp(mobile_number, otp)
        │
        └── Returns access_token (JWT) + user_id

[Tool] get_user_transactions(user_id, token)
        │
        └── Returns all past journeys (complete + incomplete)

[Tool] get_latest_incomplete_journey(mobile_number, token)
        │
        └── Returns last incomplete transaction_id + current_status
            (Customer can resume from that step)

[Tool] list_user_policies(user_id, token)
        │
        └── Returns all purchased policies with full details
```

---

## All Tools (14 total)

### New Purchase Journey

| # | Tool | Endpoint | Auth |
|---|------|----------|------|
| 1 | `submit_insurance_form` | `POST /v1/insurance-details` | None |
| 2 | `get_quotes` | `GET /v1/quotes/{transaction_id}` | None |
| 3 | `select_plan` | `PATCH /v1/transactions/select-plan` | None |
| 4 | `select_add_ons` | `PATCH /v1/transactions/select-add-ons` | None |
| 5 | `create_payment` | `POST /v1/payments` | None |
| 6 | `send_payment_otp` | `POST /v1/payments/{ref}/send-otp` | None |
| 7 | `verify_payment_otp` | `POST /v1/payments/verify-otp` | None |
| 8 | `get_payment_status` | `GET /v1/payments/{ref}/status` | None |
| 9 | `get_policy` | `GET /v1/policies/{policy_number}` | Customer JWT |

### Returning Customer

| # | Tool | Endpoint | Auth |
|---|------|----------|------|
| 10 | `send_login_otp` | `POST /v1/users/login-otp` | None |
| 11 | `verify_login_otp` | `POST /v1/users/login-otp/verify` | None |
| 12 | `get_user_transactions` | `GET /v1/users/{user_id}/transactions` | Customer JWT |
| 13 | `get_latest_incomplete_journey` | `GET /v1/users/{mobile}/latest-incomplete-journey` | Customer JWT |
| 14 | `list_user_policies` | `GET /v1/users/{user_id}/policies` | Customer JWT |

---

## Authentication

| Who | How | OTP Type | Token |
|-----|-----|----------|-------|
| New customer (purchase) | No auth — `transaction_id` is enough | N/A | None |
| Returning customer | Mobile number + OTP | 🟡 **Mock** (simulated) | Customer JWT |
| Payment | OTP on registered mobile | 🟡 **Mock** (simulated) | N/A |
| Main Backend Admin | Email + Password + OTP | 🟢 **Real** (sent to email) | Admin JWT |
| Provider Backend Admin | Email + Password + OTP | 🟢 **Real** (sent to email) | Provider JWT |

> **Note**: Admin flows are NOT part of this MCP server. Only the customer
> journey is covered here.

---

## File Structure

```
mcp/
├── README.md               ← This file
├── requirements.txt        ← Python dependencies
├── config.py               ← Backend URLs and server settings
├── main.py                 ← MCP server entry point (all tools registered)
└── tools/
    ├── insurance_tools.py  ← submit_insurance_form, get_quotes
    ├── plan_tools.py       ← select_plan, select_add_ons
    ├── payment_tools.py    ← create_payment, send/verify OTP, get_status
    ├── policy_tools.py     ← get_policy, list_user_policies
    └── customer_tools.py   ← send/verify login OTP, transactions, resume
```

---

## Setup & Running

### Prerequisites

- Python 3.10+
- `main_backend` running on `http://localhost:8000`
- `provider_backend` running on `http://localhost:8001`

### Install dependencies

```bash
cd mcp
pip install -r requirements.txt
```

### Run the MCP server

```bash
python main.py
```

Server starts at `http://0.0.0.0:8080`

---

## Connecting Claude Desktop

Add this to your Claude Desktop config
(`%AppData%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "insureflow": {
      "type": "streamable-http",
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

Restart Claude Desktop. The InsureFlow tools will appear in the tools panel.

---

## Key Design Decisions

| Decision | Reason |
|----------|--------|
| Streamable HTTP (not stdio) | Remote access — any client on the network can connect |
| `FastMCP` from official SDK | Official Anthropic pattern — handles tool registration automatically |
| `transaction_id` as primary key | Drives the entire customer journey without needing login |
| Both backends covered | `main_backend` handles journey; `provider_backend` handles quotes/plans (via main) |
| Mock OTPs for customer | Customer OTP (login + payment) is simulated for development |
| Real OTP for admin | Admin email OTP is real — sent via email service |

---

## What's NOT Included (Future)

- Admin journey (view all users, transactions, plans, forms)
- Provider admin journey (create/manage companies and plans)

These will be added in a future phase.

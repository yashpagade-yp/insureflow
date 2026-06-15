# InsureFlow MCP — Testing Guide for Claude Desktop
## All 14 Tools — Step-by-Step Testing

---

## Prerequisites

Before testing, make sure all services are running:

| Service | Command | Port |
|---|---|---|
| main_backend | `python main.py` (in `main_backend/`) | 8000 |
| MCP server | `python main.py` (in `mcp/`) | 8080 |
| ngrok tunnel | `ngrok http 8080` | — |

Your ngrok public URL will look like:
```
https://abc123.ngrok-free.app
```

---

## Claude Desktop Setup

1. Open Claude Desktop
2. Go to **Settings → Developer → Edit Config**
3. Add this to the config file:

```json
{
  "mcpServers": {
    "insureflow": {
      "url": "https://YOUR_NGROK_URL_HERE/mcp"
    }
  }
}
```

4. Replace `YOUR_NGROK_URL_HERE` with your actual ngrok URL
5. Restart Claude Desktop
6. You should see **insureflow** in the tools list ✅

---

## JOURNEY A — New Customer (Full End-to-End Test)

Test all tools in order. Copy each prompt into Claude Desktop.

---

### TOOL 1: `submit_insurance_form`

**What it does:** Creates a new user and transaction, triggers quote generation.

**Test Prompt:**
```
Use the submit_insurance_form tool with these details:
- mobile_number: "9876543210"
- insurance_type: "health"
- proposer_first_name: "Yash"
- proposer_last_name: "Pagade"
- sum_insured_requested: 500000
- policy_term_years: 1
- proposer_dob: "1995-06-15"
- proposer_email: "yash@example.com"
- proposer_gender: "male"
- city: "Pune"
- state: "Maharashtra"
```

**Expected Response:**
```json
{
  "user_id": "some-uuid",
  "transaction_id": "some-uuid",
  "message": "Form submitted successfully. Quotes generated.",
  "status": "QUOTES_GENERATED"
}
```

> ✏️ **SAVE:** Copy `user_id` and `transaction_id` — needed for all next steps.

---

### TOOL 2: `get_quotes`

**What it does:** Fetches all insurance plans available for the transaction.

**Test Prompt:**
```
Use the get_quotes tool with:
- transaction_id: "PASTE_TRANSACTION_ID_FROM_STEP_1"
```

**Expected Response:**
```json
{
  "quotes": [
    {
      "plan_id": "plan-uuid-1",
      "company_name": "Star Health",
      "plan_name": "Comprehensive Health Plan",
      "coverage_amount": 500000,
      "base_premium": 8000,
      "total_premium": 8500,
      "available_add_ons": [
        {"name": "Critical Illness Cover", "price": 500}
      ]
    }
  ]
}
```

> ✏️ **SAVE:** Copy one `plan_id` from the results — needed for next step.

---

### TOOL 3: `select_plan`

**What it does:** Saves the customer's chosen plan on the transaction.

**Test Prompt:**
```
Use the select_plan tool with:
- transaction_id: "PASTE_TRANSACTION_ID"
- selected_plan_id: "PASTE_PLAN_ID_FROM_STEP_2"
```

**Expected Response:**
```json
{
  "message": "Plan selected successfully",
  "status": "OFFER_SELECTED"
}
```

---

### TOOL 4: `select_add_ons`

**What it does:** Saves the customer's chosen add-ons (or empty list if none).

#### Test 4A — With Add-ons:
```
Use the select_add_ons tool with:
- transaction_id: "PASTE_TRANSACTION_ID"
- selected_plan_id: "PASTE_PLAN_ID"
- selected_add_ons: [{"name": "Critical Illness Cover", "price": 500}]
```

#### Test 4B — No Add-ons:
```
Use the select_add_ons tool with:
- transaction_id: "PASTE_TRANSACTION_ID"
- selected_plan_id: "PASTE_PLAN_ID"
- selected_add_ons: []
```

**Expected Response:**
```json
{
  "message": "Add-ons saved successfully",
  "status": "ADD_ONS_SELECTED"
}
```

---

### TOOL 5: `create_payment`

**What it does:** Creates a payment session. Returns payment_reference.

**Test Prompt:**
```
Use the create_payment tool with:
- transaction_id: "PASTE_TRANSACTION_ID"
- user_id: "PASTE_USER_ID_FROM_STEP_1"
- amount: 8500
```

**Expected Response:**
```json
{
  "payment_reference": "PAY-xxxxxxxx",
  "gateway_url": "https://mock-gateway.insureflow.com/pay/PAY-xxxxxxxx",
  "status": "PAYMENT_PENDING"
}
```

> ✏️ **SAVE:** Copy `payment_reference` — needed for next two steps.

---

### TOOL 6: `send_payment_otp`

**What it does:** Sends a mock OTP to the customer's mobile for payment confirmation.

**Test Prompt:**
```
Use the send_payment_otp tool with:
- payment_reference: "PASTE_PAYMENT_REFERENCE"
```

**Expected Response:**
```json
{
  "message": "Payment OTP sent to mobile number ending in 3210",
  "otp_sent": true
}
```

> ℹ️ **Note:** In mock mode, the OTP is usually `1234` or visible in the backend logs.

---

### TOOL 7: `verify_payment_otp`

**What it does:** Verifies payment OTP → completes payment → auto-issues policy.

**Test Prompt:**
```
Use the verify_payment_otp tool with:
- transaction_id: "PASTE_TRANSACTION_ID"
- payment_reference: "PASTE_PAYMENT_REFERENCE"
- otp: "1234"
```

**Expected Response:**
```json
{
  "message": "Payment verified. Policy issued successfully.",
  "policy_number": "POL-xxxxxxxx",
  "status": "PURCHASED"
}
```

> ✏️ **SAVE:** Copy `policy_number` — needed for get_policy test.

---

### TOOL 8: `get_payment_status`

**What it does:** Checks current status of a payment.

**Test Prompt:**
```
Use the get_payment_status tool with:
- payment_reference: "PASTE_PAYMENT_REFERENCE"
```

**Expected Response:**
```json
{
  "payment_reference": "PAY-xxxxxxxx",
  "status": "COMPLETED",
  "amount": 8500
}
```

---

## JOURNEY B — Returning Customer Login

Before testing protected tools (get_policy, list_user_policies etc.), login is required.

---

### TOOL 9: `send_login_otp`

**What it does:** Sends a mock login OTP to the mobile number.

**Test Prompt:**
```
Use the send_login_otp tool with:
- mobile_number: "9876543210"
```

**Expected Response:**
```json
{
  "message": "OTP sent to mobile number ending in 3210",
  "otp_sent": true
}
```

---

### TOOL 10: `verify_login_otp`

**What it does:** Verifies login OTP and returns a JWT token.

**Test Prompt:**
```
Use the verify_login_otp tool with:
- mobile_number: "9876543210"
- otp: "1234"
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": "some-uuid",
  "message": "Login successful"
}
```

> ✏️ **SAVE:** Copy `access_token` and `user_id` — needed for all protected tools below.

---

### TOOL 11: `get_policy`

**What it does:** Fetches issued policy document by policy number.

**Test Prompt:**
```
Use the get_policy tool with:
- policy_number: "PASTE_POLICY_NUMBER"
- token: "PASTE_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "policy_number": "POL-xxxxxxxx",
  "company_name": "Star Health",
  "plan_name": "Comprehensive Health Plan",
  "coverage_amount": 500000,
  "total_premium": 8500,
  "start_date": "2026-06-15",
  "end_date": "2027-06-15",
  "pdf_url": "https://mock.insureflow.com/policies/POL-xxxxxxxx.pdf"
}
```

---

### TOOL 12: `list_user_policies`

**What it does:** Lists all purchased policies for the logged-in customer.

**Test Prompt:**
```
Use the list_user_policies tool with:
- user_id: "PASTE_USER_ID"
- token: "PASTE_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "policies": [
    {
      "policy_number": "POL-xxxxxxxx",
      "plan_name": "Comprehensive Health Plan",
      "coverage_amount": 500000,
      "total_premium": 8500,
      "status": "ACTIVE"
    }
  ]
}
```

---

### TOOL 13: `get_user_transactions`

**What it does:** Lists all transactions (complete and incomplete) for the customer.

**Test Prompt:**
```
Use the get_user_transactions tool with:
- user_id: "PASTE_USER_ID"
- token: "PASTE_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "transactions": [
    {
      "transaction_id": "some-uuid",
      "insurance_type": "HEALTH",
      "current_status": "PURCHASED",
      "created_at": "2026-06-15T01:30:00Z"
    }
  ]
}
```

---

### TOOL 14: `get_latest_incomplete_journey`

**What it does:** Finds the most recent incomplete journey for a returning customer.

**Test this after starting but NOT completing a new journey.**

**Test Prompt:**
```
Use the get_latest_incomplete_journey tool with:
- mobile_number: "9876543210"
- token: "PASTE_ACCESS_TOKEN"
```

**Expected Response (if journey exists):**
```json
{
  "transaction_id": "some-uuid",
  "current_status": "QUOTES_GENERATED",
  "insurance_type": "HEALTH",
  "created_at": "2026-06-15T00:00:00Z"
}
```

**Expected Response (if no incomplete journey):**
```json
{
  "message": "No incomplete journey found"
}
```

---

## Quick One-Shot Test Prompt (Full Journey)

Paste this into Claude Desktop to test the entire new customer journey in one go:

```
I want to test the InsureFlow MCP tools. Please help me go through the
complete new customer insurance journey using the available tools.

Customer details:
- Name: Yash Pagade
- Mobile: 9876543210
- Insurance Type: health
- Sum Insured: 500000 rupees
- Policy Term: 1 year
- Date of Birth: 1995-06-15
- City: Pune, State: Maharashtra

Start from submit_insurance_form and go all the way through to
verify_payment_otp. Use OTP "1234" for all OTP steps.
Pick the first available plan and skip add-ons.
Tell me the result of each step clearly.
```

---

## Error Testing

### Test with invalid OTP:
```
Use the verify_login_otp tool with:
- mobile_number: "9876543210"
- otp: "9999"
```
**Expected:** Error response — invalid OTP

### Test with invalid transaction_id:
```
Use the get_quotes tool with:
- transaction_id: "invalid-id-here"
```
**Expected:** Error response — transaction not found

---

## Tool Status Checklist

| # | Tool | Tested | Result |
|---|---|---|---|
| 1 | `submit_insurance_form` | ☐ | |
| 2 | `get_quotes` | ☐ | |
| 3 | `select_plan` | ☐ | |
| 4 | `select_add_ons` | ☐ | |
| 5 | `create_payment` | ☐ | |
| 6 | `send_payment_otp` | ☐ | |
| 7 | `verify_payment_otp` | ☐ | |
| 8 | `get_payment_status` | ☐ | |
| 9 | `send_login_otp` | ☐ | |
| 10 | `verify_login_otp` | ☐ | |
| 11 | `get_policy` | ☐ | |
| 12 | `list_user_policies` | ☐ | |
| 13 | `get_user_transactions` | ☐ | |
| 14 | `get_latest_incomplete_journey` | ☐ | |

Mark each ☐ as ✅ (pass) or ❌ (fail) while testing.

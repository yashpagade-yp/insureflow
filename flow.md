# InsureFlow — Customer & Admin Flow

> This document captures the complete, agreed-upon flow for the InsureFlow project.
> It is the reference for the CLI and MCP implementations.

---

## Customer Flow (New Customer)

```
1.  Customer opens the app / CLI
2.  Customer fills the insurance form directly (NO registration required)
        - Mobile Number
        - Insurance Type (Health / Life / General)
        - First Name, Last Name
        - Email, DOB, Gender (optional)
        - Sum Insured, Policy Term, City, State (optional)
3.  main_backend creates a Transaction and saves Insurance Details step by step
4.  Customer verifies mobile via OTP (mock OTP) to get JWT token
5.  Customer requests Quotes
6.  main_backend sends filtered data to provider_backend
7.  provider_backend returns matching quotes / plans
8.  Customer views plans and selects one plan
9.  Customer optionally selects Add-ons
10. Customer proceeds to Payment
11. Payment record is created and Payment OTP is generated
12. Customer enters Payment OTP to confirm
13. Payment becomes successful
14. Policy is issued automatically
15. PDF is generated and stored
16. Transaction is marked as PURCHASED / COMPLETED
```

---

## Customer Flow (Returning Customer)

```
1.  Customer opens the app / CLI
2.  Customer selects "Returning Customer"
3.  Customer enters Mobile Number
4.  mock OTP is sent → Customer enters OTP → JWT token is issued
5.  Customer can view:
        a. Latest incomplete journey
               - Transaction ID
               - Insurance Type
               - Current Status
               - Selected Plan
               - Payment Status
        b. All transactions with status
               - Transaction ID
               - Insurance Type
               - Status (FORM_SUBMITTED / OFFER_SELECTED / PAYMENT_PENDING / PURCHASED)
               - Selected Plan ID
               - Payment Reference
        c. All issued policies
               - Policy Number
               - Company Name
               - Plan Name
               - Coverage Amount
               - Total Premium
               - Term (years)
               - Status (ACTIVE)
               - Policy PDF URL
6.  If journey is incomplete, customer can RESUME from where they left off:
        - FORM_SUBMITTED / UNKNOWN   → Fetch quotes → Select plan → Add-ons → Payment
        - OFFER_SELECTED             → Select add-ons → Payment
        - ADD_ONS_SELECTED           → Payment
        - PAYMENT_PENDING            → Enter Payment OTP directly
        - PURCHASED / COMPLETED      → Show issued policy
```

---

## Admin Flow (Inside Customer App)

> Note: Admin flow is NOT implemented in CLI or MCP currently.
> This is the agreed reference for future implementation.

```
1.  Admin opens the app
2.  Admin logs in with:
        - Email
        - Password
        - OTP (sent to admin email — real OTP, not mock)
3.  Admin JWT token is issued
4.  This admin belongs only to the customer app / `main_backend`
5.  Admin can monitor:
        a. Customers
               - List all customers
               - View customer profile
               - View customer transactions
        b. Transactions
               - List all transactions
               - Filter by status (PENDING / PAYMENT_PENDING / PURCHASED)
               - View full transaction detail
        c. Pending Forms
               - List incomplete / abandoned journeys
               - See which step the customer dropped off
        d. Policies
               - List all issued policies
               - View policy detail
               - Attach / view policy PDF
        e. Support / Issues
               - View support tickets
               - Respond to customer issues
```

This admin flow is separate from the provider admin flow.

---

## API Backend Mapping

| Flow Step                     | Backend         | Endpoint                                        | Auth     |
|-------------------------------|-----------------|--------------------------------------------------|----------|
| Submit insurance form         | main_backend    | `POST /v1/insurance-details`                    | None     |
| Send login OTP                | main_backend    | `POST /v1/users/login-otp`                      | None     |
| Verify login OTP              | main_backend    | `POST /v1/users/login-otp/verify`               | None     |
| Get quotes                    | main_backend    | `GET /v1/quotes/{transaction_id}`               | JWT      |
| Select plan                   | main_backend    | `PATCH /v1/transactions/select-plan`            | JWT      |
| Select add-ons                | main_backend    | `PATCH /v1/transactions/select-add-ons`         | JWT      |
| Create payment                | main_backend    | `POST /v1/payments`                             | JWT      |
| Send payment OTP              | main_backend    | `POST /v1/payments/{ref}/send-otp`              | JWT      |
| Verify payment OTP            | main_backend    | `POST /v1/payments/verify-otp`                  | JWT      |
| Get payment status            | main_backend    | `GET /v1/payments/{ref}/status`                 | JWT      |
| List user policies            | main_backend    | `GET /v1/users/{user_id}/policies`              | JWT      |
| Get single policy             | main_backend    | `GET /v1/policies/{policy_number}`              | JWT      |
| List user transactions        | main_backend    | `GET /v1/users/{user_id}/transactions`          | JWT      |
| Get single transaction        | main_backend    | `GET /v1/transactions/{transaction_id}`         | JWT      |
| Get incomplete journey        | main_backend    | `GET /v1/users/{mobile}/latest-incomplete-journey` | JWT   |
| Admin login                   | main_backend    | `POST /v1/admins/login`                         | None     |
| Verify admin OTP              | main_backend    | `POST /v1/admins/login/verify`                  | None     |
| List plans (for quotes)       | provider_backend| `GET /v1/plans/`                                | None     |
| Get plan detail               | provider_backend| `GET /v1/plans/{plan_id}`                       | None     |
| List buyer companies          | provider_backend| `GET /v1/buyer-companies/`                      | Admin JWT|
| List provider companies       | provider_backend| `GET /v1/provider-companies/`                   | Admin JWT|

---

## Auth Rules

| User Type  | Login Method                     | OTP Type | Token |
|------------|----------------------------------|----------|-------|
| Customer   | Mobile Number                    | Mock OTP | JWT   |
| Admin      | Email + Password + Email OTP     | Real OTP | JWT   |

---

## What Is Built

| Component  | Status      | Notes                                          |
|------------|-------------|------------------------------------------------|
| CLI        | Done        | Full customer flow (new + returning + resume)  |
| MCP Server | Done        | 14 tools, Streamable HTTP on port 8080         |
| ngrok URL  | Pending     | To be added to MCP config when available       |
| Admin Flow | Not started | Customer-app admin only; separate from provider admin |

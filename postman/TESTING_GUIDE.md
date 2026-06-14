# InsureFlow API Testing Guide

## Files

- `postman/InsureFlow_API_Testing.postman_collection.json`
- `postman/InsureFlow_Local.postman_environment.json`

## Import Order

1. Import the environment file.
2. Import the collection file.
3. Select the `InsureFlow Local` environment in Postman.

## Prerequisites

Before running the collection, make sure:

1. `main_backend` is running on `http://127.0.0.1:5100`
2. `provider_backend` is running on `http://127.0.0.1:5200`
3. MongoDB is running and reachable by both backends
4. A provider admin user already exists in provider DB
5. If you want to test main-admin endpoints later, a main admin user already exists in main DB

## Very Important OTP Limitation

Current implementation does **not** return plain OTP values in API responses.

Also:

- OTPs are hashed before storage
- plain OTPs are not logged in the current code

That means full end-to-end testing cannot be completed from Postman alone unless you add a temporary dev-only OTP helper.

Practical options for local testing:

1. Temporarily log plain OTP before hashing
2. Temporarily return plain OTP in dev-only responses
3. Integrate a real delivery channel that you can read during testing

Until one of those exists, you must manually fill:

- `provider_admin_otp`
- `customer_login_otp`
- `payment_otp`

## Sequence

### Phase 1: Provider Setup

Run these requests in order:

1. `Provider Admin Login`
2. `Provider Admin Verify OTP`
3. `Create Mediator Company (InsureFlow)`
4. `Create Provider Company`
5. `Create Provider Plan`
6. `List Provider Plans`

### Critical Step After Mediator Creation

When `Create Mediator Company (InsureFlow)` succeeds:

1. Copy `plain_api_key` from the response
2. Open `backend/main_backend/.env`
3. Set:

```env
INSUREFLOW_API_KEY=<plain_api_key_from_response>
```

4. Restart `main_backend`

Without this, quote/payment calls from main backend to provider backend will fail.

### Phase 2: Customer Journey

Run these requests in order:

1. `Create Insurance Detail Journey`
2. `Customer Login OTP`
3. `Customer Verify Login OTP`
4. `Get Quotes`
5. `Select Plan`
6. `Select Add-ons`
7. `Get Transaction`
8. `Create Payment`
9. `Send Payment OTP`
10. `Verify Payment OTP`
11. `Get Payment Status`
12. `List User Policies`
13. `Get Policy`

## What Gets Auto-Saved by the Collection

The collection stores these variables automatically when responses succeed:

- `provider_admin_token`
- `provider_admin_id`
- `insureflow_api_key`
- `user_id`
- `transaction_id`
- `insurance_detail_id`
- `selected_plan_id`
- `quote_total_premium`
- `selected_add_ons_json`
- `payment_reference`
- `policy_number`

## Notes on Add-ons

The `Get Quotes` request tries to prepare `selected_add_ons_json` automatically:

- if add-ons exist, it picks the first available add-on
- if no add-ons exist, it sets `[]`

So `Select Add-ons` should work in both cases.

## Suggested Smoke Check

If you want a quick minimum validation:

1. Provider Setup through `Create Provider Plan`
2. Set `INSUREFLOW_API_KEY`
3. Restart `main_backend`
4. Run customer requests through `Get Quotes`

If quotes are returned, your inter-service integration is working.

## Full Success Criteria

A successful full run should produce:

1. a created transaction
2. generated quote items
3. selected plan and add-ons
4. created payment reference
5. successful payment verification
6. issued `policy_number`
7. successful policy fetch

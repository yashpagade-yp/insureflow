# InsureFlow Overview

## What Is InsureFlow?

InsureFlow is an insurance management platform that connects customers with insurance provider companies through buyer or mediator companies such as InsureFlow. It helps customers explore insurance options, receive quotes, select plans, make payments, and receive policy documents through a structured digital flow.

In short, InsureFlow acts as the bridge between customers and insurance provider companies. It manages the customer journey on one side and communicates with the provider side on the other side.

---

## System Structure

InsureFlow contains:

- Two frontends
- Two backends

### Customer Frontend

The customer frontend is the user-facing application where customers complete
their insurance journey. It also contains a customer-operations admin view for
monitoring users, transactions, forms, policies, and support issues.

### Provider Admin Frontend

The provider admin frontend is a separate admin-facing application used only by
authenticated admin users. This frontend is used to manage provider companies,
manage buyer companies, manage plans, and access provider-side
administrative operations.

### Main Backend

The main backend is for the InsureFlow company. It handles customer journeys, user data, transactions, insurance details, policies, and support-related operations.

### Provider Backend

The provider backend is for the provider-side administrative and integration
layer. It handles provider-admin authentication, provider companies, buyer
company registration, insurance plans, quotes, payment-related provider
operations, and secure API-key-based communication.

---

## What InsureFlow Does

InsureFlow helps manage the complete insurance purchase journey:

1. Customer enters insurance-related details.
2. The system creates a transaction.
3. The main backend communicates with the provider backend.
4. Matching insurance quotes are generated.
5. Customer selects a plan and optional add-ons.
6. The transaction moves to payment pending and a payment record is created.
7. A mock payment gateway page is opened through a payment URL.
8. A payment OTP is sent to the customer's mobile number and must be verified on the mock gateway page.
9. Payment is confirmed after successful OTP verification.
10. Policy PDF is generated and issued to the customer.
11. If needed, support tickets can be raised and handled.

---

## Project Flow

### Customer Flow

1. Customer visits the platform.
2. Customer fills in the insurance details form.
3. A transaction is created in the system.
4. The transaction is linked to the customer, and the same customer can create multiple separate transactions over time using the same mobile number.
5. InsureFlow sends the request to the provider backend.
6. Provider backend checks available insurance plans and returns quotes.
7. Customer reviews the quotes.
8. Customer selects a plan.
9. Customer selects add-ons if available.
10. Customer confirms the selected offer.
11. The transaction moves to `PAYMENT_PENDING`.
12. A payment record is created in the provider backend and linked through `transaction_id` and `user_id`.
13. A planned payment URL opens a mock payment gateway page.
14. The mock payment gateway sends a payment OTP to the customer's mobile number.
15. Customer enters the payment OTP on the gateway page.
16. If the OTP is valid, payment is marked successful.
17. Policy PDF is generated and shared with the customer.
18. Customer can later log in again using a separate login OTP on the same mobile number.
19. After login, the customer can track progress, resume from the last saved status, or download the issued policy.

### Admin Flow

1. The customer-app admin logs in using email and password.
2. The customer frontend admin view lets the customer-app admin monitor users,
   transactions, pending forms, completed forms, policies, and customer issues.
3. The customer-app admin belongs only to the main backend and customer-side
   operations.
4. The provider admin frontend is separate and requires its own provider-side
   admin login using email, password, and OTP.
5. The provider admin belongs only to the provider backend and provider-side
   operations.
6. Through the provider admin frontend, admin creates and updates insurance
   plans in the provider backend.
7. Admin registers insurance provider companies in the provider backend.
8. Admin also creates and registers buyer companies such as InsureFlow or
   similar mediator platforms.
9. During buyer-company registration, the provider backend generates an API key.
10. The plain API key is shared once with the registered buyer company.
11. Only the hashed version of that API key is stored in the provider backend.
12. Future request-response communication between the buyer company and the
    provider backend happens through that API key.
13. The provider backend verifies the API key securely before allowing
    communication.
14. The provider admin dashboard separates buyer companies and provider
    companies into their own management areas.
15. The provider admin can activate or deactivate provider insurance companies.
16. Admin can monitor transaction progress, including incomplete journeys that
    users may later resume.

---

## User Role

The user role is for customers who want to buy insurance.

Users can:

- Fill in their insurance details
- Start multiple insurance purchase journeys using the same mobile number
- Receive insurance quotes
- Select plans and add-ons
- Complete mock payments through a payment URL and payment OTP verification
- Receive issued policy documents and generated policy PDFs
- Log in later using mobile OTP
- Resume from the last saved transaction status
- Track their transaction status
- Raise support tickets

---

## Admin Role

InsureFlow has two separate admin roles.

### Customer-App Admin

The customer-app admin is for customer-side monitoring and operations in the
main backend.

Customer-app admins can:

- Log in with email, password, and OTP
- Use the customer frontend admin view to monitor users, transactions, pending
  forms, policies, and support issues
- Handle customer-side tickets and operational issues

### Provider Admin

The provider admin is for provider-side setup and administration in the
provider backend.

Provider admins can:

- Log in separately to the provider admin frontend with email, password, and OTP
- View users and transactions
- View multiple transactions created by the same user mobile number
- Create and update insurance plans
- Register insurance provider companies
- Create and register buyer companies like InsureFlow
- Activate or deactivate provider insurance companies
- Control secure communication between buyer companies and provider companies through API-key-based access
- Manage provider-side administrative operations through the provider backend

These two admins are separate and should not be treated as the same admin
identity.

---

## API Key Communication

The provider backend supports secure communication between buyer companies and insurance provider companies.

When a company is registered:

1. The provider backend generates an API key for a registered buyer company.
2. The plain API key is given once to the registered buyer company.
3. The provider backend stores only the hashed version of the API key.
4. Later, whenever the buyer company sends a request, the API key is verified.
5. If the key is valid, request-response communication is allowed securely.

This makes InsureFlow a controlled and secure buyer platform between customers and insurance provider companies.

## OTP Usage

InsureFlow uses OTP in two different customer-facing situations:

1. Login OTP
2. Payment OTP

The login OTP is used when the customer logs in using the registered mobile number to access progress, resume an incomplete transaction, or view issued policies.

The payment OTP is used only inside the mock payment gateway page to confirm a payment attempt.

Both OTPs are sent to the customer's mobile number, but they are different flows with different purposes and should be treated separately in the system.

## Resume Journey Behavior

InsureFlow supports resume-friendly customer journeys.

If a customer fills in insurance details, reaches any intermediate stage, and leaves before completing the purchase, the journey is not lost.

When the customer returns later and logs in again using mobile OTP:

1. The system identifies the customer by mobile number.
2. The system fetches the customer's existing transactions.
3. The customer can continue from the latest incomplete transaction status.
4. Completed transactions remain available as purchase history.

This allows one customer to use the same mobile number for multiple policy purchases while preserving each journey under its own transaction ID.

## Key Design Decisions

| Decision                    | Reason                                                                    |
| --------------------------- | ------------------------------------------------------------------------- |
| Dual frontend + dual backend| Separation of customer journey UI, provider admin UI, and backend responsibilities |
| OTP embedded in User        | Avoids a separate collection query on every login; simpler architecture   |
| Add-ons embedded in Plan    | Add-ons are plan-specific, not independent entities                       |
| Quote as list               | One atomic document per transaction; easier to query and update           |
| String refs across backends | ObjectId refs don't work across databases; String IDs are simpler         |
| Mock payment gateway        | Real payment integration is out of scope; payment is simulated through a gateway URL and payment OTP flow |

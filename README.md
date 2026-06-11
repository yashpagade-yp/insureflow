# InsureFlow Overview

## What Is InsureFlow?

InsureFlow is an insurance management platform that connects customers with insurance provider companies through a mediator company such as InsureFlow. It helps customers explore insurance options, receive quotes, select plans, make payments, and receive policy documents through a structured digital flow.

In short, InsureFlow acts as the bridge between customers and insurance provider companies. It manages the customer journey on one side and communicates with the provider side on the other side.

---

## System Structure

InsureFlow contains:

- One frontend
- Two backends

### Frontend

The frontend is the user-facing application where customers and admins interact with the platform.

### Main Backend

The main backend is for the InsureFlow company. It handles customer journeys, user data, transactions, insurance details, policies, and support-related operations.

### Provider Backend

The provider backend is for the insurance policy provider company side. It handles provider companies, mediator company registration, insurance plans, quotes, and payment-related provider operations.

---

## What InsureFlow Does

InsureFlow helps manage the complete insurance purchase journey:

1. Customer enters insurance-related details.
2. The system creates a transaction.
3. The main backend communicates with the provider backend.
4. Matching insurance quotes are generated.
5. Customer selects a plan and optional add-ons.
6. Payment is processed.
7. Policy is issued to the customer.
8. If needed, support tickets can be raised and handled.

---

## Project Flow

### Customer Flow

1. Customer visits the platform.
2. Customer fills in the insurance details form.
3. A transaction is created in the system.
4. InsureFlow sends the request to the provider backend.
5. Provider backend checks available insurance plans and returns quotes.
6. Customer reviews the quotes.
7. Customer selects a plan.
8. Customer selects add-ons if available.
9. Customer confirms the selected offer.
10. Payment is completed.
11. Policy is generated and shared with the customer.
12. Customer can later log in again and track progress or download the policy.

### Admin Flow

1. Admin logs in using email and password.
2. System sends an OTP to the admin’s registered email.
3. Admin verifies the OTP and enters the admin dashboard.
4. Admin manages users, transactions, and support tickets.
5. Admin creates and updates insurance plans in the provider backend.
6. Admin registers insurance provider companies in the provider backend.
7. Admin also registers mediator companies like InsureFlow or similar companies that connect customers with insurance providers.
8. During company registration, the provider backend generates an API key.
9. The plain API key is shared once with the registered mediator company.
10. Only the hashed version of that API key is stored in the provider backend.
11. Future request-response communication between the mediator company and the provider backend happens through that API key.
12. The provider backend verifies the API key securely before allowing communication.

---

## User Role

The user role is for customers who want to buy insurance.

Users can:

- Fill in their insurance details
- Receive insurance quotes
- Select plans and add-ons
- Make payments
- Receive policy documents
- Log in later using mobile OTP
- Track their transaction status
- Raise support tickets

---

## Admin Role

The admin role is for platform management and provider-side coordination.

Admins can:

- Log in with email, password, and OTP
- Manage customer and admin-related operations
- View users and transactions
- Handle support tickets
- Create and update insurance plans
- Register insurance provider companies
- Register mediator companies like InsureFlow
- Control secure communication between companies through API-key-based access

---

## API Key Communication

The provider backend supports secure communication between InsureFlow-like mediator companies and insurance provider companies.

When a company is registered:

1. The provider backend generates an API key.
2. The plain API key is given once to the registered company.
3. The provider backend stores only the hashed version of the API key.
4. Later, whenever the mediator company sends a request, the API key is verified.
5. If the key is valid, request-response communication is allowed securely.

This makes InsureFlow a controlled and secure mediator platform between customers and insurance provider companies.

## Key Design Decisions

| Decision                    | Reason                                                                    |
| --------------------------- | ------------------------------------------------------------------------- |
| Dual backend                | Separation of concerns — customer data vs. insurance product data         |
| OTP embedded in User        | Avoids a separate collection query on every login; simpler architecture   |
| Add-ons embedded in Plan    | Add-ons are plan-specific, not independent entities                       |
| Quote as list               | One atomic document per transaction; easier to query and update           |
| String refs across backends | ObjectId refs don't work across databases; String IDs are simpler         |
| Mock payment gateway        | Real payment integration is out of scope; `mock_gateway` placeholder used |

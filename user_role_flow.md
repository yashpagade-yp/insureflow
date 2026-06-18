# User Role Flow

## Purpose

This document explains the end-to-end user-role flows in the InsureFlow
project across the customer-facing application and the provider-admin
application.

It covers:

- customer flow in the main platform
- admin flow inside the customer app
- admin flow inside the provider backend app

## 1. Customer Flow In The Main Platform

### Entry Point

1. The customer opens the customer frontend.
2. The customer starts the insurance journey directly.
3. No prior registration is required before filling the form.
4. Customer login is not the first step of the buying journey.
5. Customer authentication is mock and used mainly for returning-user access.

### Form Submission And Journey Tracking

1. The customer fills the insurance form step by step.
2. The `main_backend` creates a new transaction for the journey.
3. The `main_backend` stores insurance details progressively.
4. Form progress is saved using the transaction and form-step mechanism.

### Quote Generation Flow

1. After entering the required insurance details, the customer requests quotes.
2. The `main_backend` prepares filtered insurance input data.
3. The `main_backend` sends that data to the `provider_backend`.
4. The `provider_backend` matches plans and generates quotes.
5. The `provider_backend` returns matching quotes and offers.
6. The customer sees the available plans on the customer frontend.

### Plan And Add-On Selection

1. The customer reviews the returned plans.
2. The customer selects one plan.
3. The customer may optionally select add-ons if the chosen plan supports them.
4. The selected plan and selected add-ons are linked to the transaction.

### Payment Flow

1. The customer proceeds to payment.
2. A payment record is created.
3. A payment OTP is generated.
4. The customer enters the payment OTP.
5. The payment is verified.
6. The transaction payment status becomes successful.

### Policy Issuance Flow

1. After successful payment, policy issuance is triggered.
2. A policy record is created.
3. A policy PDF is generated.
4. The PDF location is stored.
5. The transaction is marked as complete.

### Returning Customer Flow

If the customer comes back later:

1. The customer logs in with mobile number and OTP.
2. This customer OTP flow is mock.
2. The customer can view the latest incomplete journey.
3. The customer can check transaction status.
4. The customer can see the selected plan.
5. The customer can check payment status.
6. The customer can view the issued policy.
7. The customer can access or download the policy PDF.
8. If the customer faces an issue, the customer can raise a support ticket.

### Customer Issue Or Ticket Flow

Examples of customer issues include:

1. payment is completed
2. but the transaction status does not change to purchased
3. or the policy PDF is not generated
4. or another post-purchase issue occurs

In such cases:

1. the customer raises an issue or ticket
2. a ticket record is created in the customer-side system
3. the ticket becomes visible to the customer-app admin
4. the admin investigates the issue
5. the admin resolves the issue and closes the ticket

### Customer Flow Summary

The customer fills the form first, gets quotes, selects a plan, optionally
adds add-ons, completes payment, receives the policy, and later logs in using
mock mobile OTP to track status, access the policy PDF, and raise a ticket if
an issue occurs.

## 2. Admin Flow Inside The Customer App

### Entry Point

1. The customer-app admin opens the customer-facing platform admin area.
2. The customer-app admin logs in using email, password, and OTP.
3. The customer-app admin OTP is real and is sent to the admin email.
4. This admin account belongs only to the `main_backend`.
5. This login flow is separate from the provider-admin login flow.

### Admin Responsibilities

After successful login, the customer-app admin can monitor and manage
customer-side
operations such as:

1. customer records
2. transactions
3. pending forms
4. completed journeys
5. issued policies
6. support tickets or issues
7. customer tickets raised after failed or inconsistent policy purchase outcomes
8. issue resolution and ticket closure

### Admin Flow Summary

The customer-app admin is responsible for overseeing the customer journey side
of the business, including users, transactions, forms, policies, support
operations, ticket handling, and customer issue resolution.

The customer-app admin is separate from the provider admin and should not
automatically receive provider-side access.

## 3. Provider Backend Admin Flow

### Entry Point

1. The provider admin opens the provider frontend.
2. The provider admin logs in with email and password.
3. The `provider_backend` sends an OTP to the provider admin email.
4. The provider admin enters the OTP.
5. After verification, the provider admin enters the provider admin dashboard.
6. The provider admin OTP is real and is sent to the real admin email.
7. This admin account belongs only to the `provider_backend`.
8. This login flow is separate from the customer-app admin login flow.

### Provider Admin Responsibilities

Inside the provider admin dashboard, the admin can:

1. create and register buyer companies
2. create and register provider insurance companies
3. keep buyer companies and provider companies in separate dashboard sections
4. create insurance plans under provider companies
5. add separate optional add-ons to plans where applicable
6. manage plans where some companies or plans have add-ons and some do not
7. activate provider insurance companies
8. deactivate provider insurance companies
9. ensure proper API-key-based communication between buyer companies and
   provider companies
10. monitor provider-side quote and payment records if those views are exposed
    in the dashboard

### Provider-Side Role Rules

1. The admin is the only authenticated user role on the provider side.
2. No customer logs in to the provider application.
3. No separate provider employee role is currently used.
4. This admin controls provider-side setup, onboarding, and management.
5. This admin is separate from the customer-app admin.
6. Buyer-to-provider communication should happen through API keys.
7. Activate/deactivate authority belongs to the provider admin for provider
   insurance companies.

### Provider Admin Flow Summary

The provider admin logs in with email, password, and OTP, then manages
buyer companies, provider companies, plans, add-ons, provider-company
activation status, and provider-side insurance configuration.

The provider admin is separate from the customer-app admin and should not
automatically receive customer-side access.

## 4. Platform-Level Role View

### Customer Role

The customer role exists only in the customer-facing application and is used
for:

1. filling the insurance journey form
2. viewing quotes
3. selecting plans and add-ons
4. completing payment
5. accessing policy status and PDF later
6. raising a ticket if an issue occurs

### Customer-App Admin Role

The customer-app admin role exists in the main platform and is used for:

1. operational visibility over customers
2. monitoring transactions and form completion
3. viewing policies
4. handling customer-side issues
5. viewing and resolving customer tickets
6. customer-side administration only

### Provider Admin Role

The provider admin role exists in the provider platform and is used for:

1. buyer-company onboarding
2. provider-company onboarding
3. provider-company activation and deactivation
4. plan and add-on management
5. provider-side administration only

## 5. Final Simple Summary

InsureFlow has two main operational sides:

- the customer side, where customers complete insurance journeys and customer
  admins monitor them and resolve tickets raised by customers
- the provider side, where the provider admin configures provider companies,
  buyer companies, plans, add-ons, provider-company status, and provider-side
  setup

These two admin flows are separate. A customer-app admin belongs only to the
main/customer side, and a provider admin belongs only to the provider side.

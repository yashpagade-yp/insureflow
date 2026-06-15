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
2. The customer can view the latest incomplete journey.
3. The customer can check transaction status.
4. The customer can see the selected plan.
5. The customer can check payment status.
6. The customer can view the issued policy.
7. The customer can access or download the policy PDF.

### Customer Flow Summary

The customer fills the form first, gets quotes, selects a plan, optionally
adds add-ons, completes payment, receives the policy, and later logs in using
mobile OTP to track status and access the policy PDF.

## 2. Admin Flow Inside The Customer App

### Entry Point

1. The admin opens the customer-facing platform admin area.
2. The admin logs in using email, password, and OTP.

### Admin Responsibilities

After successful login, the admin can monitor and manage customer-side
operations such as:

1. customer records
2. transactions
3. pending forms
4. completed journeys
5. issued policies
6. support tickets or issues

### Admin Flow Summary

The customer-app admin is responsible for overseeing the customer journey side
of the business, including users, transactions, forms, policies, and support
operations.

## 3. Provider Backend Admin Flow

### Entry Point

1. The admin opens the provider frontend.
2. The admin logs in with email and password.
3. The `provider_backend` sends an OTP to the admin email.
4. The admin enters the OTP.
5. After verification, the admin enters the provider admin dashboard.

### Provider Admin Responsibilities

Inside the provider admin dashboard, the admin can:

1. register the mediator company `InsureFlow`
2. generate and copy the one-time API key used for broker-to-provider
   communication
3. register provider insurance companies
4. create insurance plans under provider companies
5. add optional add-ons to plans
6. view all registered companies
7. view all published plans
8. monitor provider-side quote and payment records if those views are exposed
   in the dashboard

### Provider-Side Role Rules

1. The admin is the only authenticated user role on the provider side.
2. No customer logs in to the provider application.
3. No separate provider employee role is currently used.
4. This admin controls provider-side setup, onboarding, and management.

### Provider Admin Flow Summary

The provider admin logs in with email, password, and OTP, then manages
mediator registration, provider companies, plans, add-ons, and provider-side
insurance setup.

## 4. Platform-Level Role View

### Customer Role

The customer role exists only in the customer-facing application and is used
for:

1. filling the insurance journey form
2. viewing quotes
3. selecting plans and add-ons
4. completing payment
5. accessing policy status and PDF later

### Customer-App Admin Role

The customer-app admin role exists in the main platform and is used for:

1. operational visibility over customers
2. monitoring transactions and form completion
3. viewing policies
4. handling customer-side issues

### Provider Admin Role

The provider admin role exists in the provider platform and is used for:

1. insurer onboarding
2. mediator registration
3. API-key-based integration setup
4. plan and add-on management

## 5. Final Simple Summary

InsureFlow has two main operational sides:

- the customer side, where customers complete insurance journeys and customer
  admins monitor them
- the provider side, where the provider admin configures mediator records,
  provider companies, plans, add-ons, and provider integration setup

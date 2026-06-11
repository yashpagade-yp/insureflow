# InsureFlow Architecture Decision Record

## Purpose

This document captures the architectural decisions and coding rules for the InsureFlow project.

It is focused only on:

- `main_backend`
- `provider_backend`
- backend communication
- backend coding standards

---

## Backend Context

The backend side of InsureFlow is designed to support the full insurance lifecycle:

1. insurance detail submission
2. transaction creation
3. quote generation
4. plan and add-on selection
5. payment processing
6. policy issuance
7. support ticket handling

The platform uses two separate FastAPI backend services and a shared MongoDB Atlas cluster with separate databases.

---

## Backend Architecture Decisions

### 1. Dual Backend Architecture

**Decision**

The project uses two backend services:

- `main_backend`
- `provider_backend`

**Why**

- separates customer journey logic from provider-side logic
- keeps responsibilities cleaner
- improves maintainability
- makes provider-side changes easier to manage independently

---

### 2. Backend Responsibility Split

**Decision**

Each backend has a specific responsibility boundary.

`main_backend` handles:

- users
- admin authentication
- customer authentication
- transactions
- insurance details
- policies
- support tickets

`provider_backend` handles:

- registered companies
- insurance provider company onboarding
- mediator company onboarding such as InsureFlow
- insurance plans
- quote generation
- provider-side payment records

**Why**

- avoids mixing provider logic with customer workflow logic
- keeps business operations easier to understand
- supports clear ownership of data and APIs

---

### 3. Shared Cluster, Separate Databases

**Decision**

Both backends use the same MongoDB Atlas cluster but separate databases.

**Why**

- keeps services logically separated
- avoids mixing provider data with main platform data
- supports a microservice-style structure without extra infrastructure complexity

---

### 4. Cross-Backend Linking by Transaction ID

**Decision**

The backends are linked using a shared `transaction_id` string instead of cross-database `ObjectId` references.

**Why**

- easier to pass through APIs
- simpler to debug and trace
- avoids cross-database reference complications

---

### 5. Inter-Service Communication Through API Calls

**Decision**

The `main_backend` communicates with the `provider_backend` through API calls.

**Why**

- keeps both services independent
- avoids direct provider database access from the main backend
- makes service boundaries cleaner

---

### 6. API-Key-Based Company Communication

**Decision**

The provider backend supports secure communication for registered companies using API keys.

**How It Works**

- admin registers insurance provider companies in the provider backend
- admin also registers mediator companies such as InsureFlow or similar platforms
- during registration, the provider backend generates an API key
- the plain API key is shared once with the registered company
- only the hashed API key is stored in the provider backend
- future request-response communication is allowed only after API key verification

**Why**

- secures inter-service communication
- prevents plain API key storage
- supports controlled access for external and mediator systems

---

### 7. Transaction-Centric Journey Tracking

**Decision**

The insurance purchase flow is tracked through a dedicated transaction lifecycle.

**Why**

- gives one central record for the full journey
- makes progress tracking easier
- supports resume flow and auditability

**Expected Status Progression**

1. `FORM_SUBMITTED`
2. `OFFERS_RECEIVED`
3. `OFFER_SELECTED`
4. `ADD_ONS_SELECTED`
5. `OFFER_CONFIRMED`
6. `PAYMENT_PENDING`
7. `PURCHASED`

Optional failure state:

- `PAYMENT_FAILED`

---

### 8. OTP Embedded in User Model

**Decision**

OTP state is stored inside the user document instead of in a separate auth collection.

**Why**

- keeps authentication state close to the user
- reduces extra collection lookups
- simplifies the current implementation

---

### 9. Add-Ons Embedded in Insurance Plans

**Decision**

Add-ons are stored inside insurance plan documents rather than in a separate collection.

**Why**

- add-ons are plan-specific
- simplifies quote generation
- avoids unnecessary extra queries

---

### 10. Quote Stored as One Document per Transaction

**Decision**

All quote items for one transaction are grouped inside a single quote document.

**Why**

- keeps quote retrieval simple
- supports atomic quote access
- makes selection flow easier to manage

---

### 11. Mock Payment for Current Scope

**Decision**

Payment is currently handled as a mock flow.

**Why**

- real payment gateway integration is outside current scope
- helps complete the end-to-end backend flow first
- keeps development focused on business logic

---

### 12. Backend Policy Generation

**Decision**

Policy creation and PDF generation are backend responsibilities.

**Why**

- policy issuance should stay controlled and auditable
- document generation belongs to business logic, not frontend behavior

---

### 13. Strict Admin Access

**Decision**

Admin access is restricted and stronger than normal customer access.

**Admin Principles**

- no public admin sign-up
- admin creation only by existing authenticated admins
- admin login uses email, password, and OTP
- admin routes must enforce explicit admin authorization

**Why**

- protects sensitive management features
- reduces unauthorized access risk
- fits the responsibilities of admin operations

---

## Backend Coding Rules

These rules should be followed while writing or updating backend code.

### 1. Keep Layer Responsibilities Clear

**Route Layer**

- handle request and response
- apply dependencies
- call controller functions

**Controller Layer**

- handle business flow
- coordinate CRUD and service logic
- manage state transitions

**CRUD Layer**

- perform database operations only

**Rule**

- do not mix database logic directly into routers
- do not overload controllers with raw persistence code when CRUD exists

---

### 2. Write Clear Docstrings

Important route handlers, controller functions, and non-trivial helpers should include useful docstrings.

Docstrings should explain:

- what the function does
- input meaning
- return value
- possible raised errors when relevant

---

### 3. Use Structured Exception Handling

Use `try/except` patterns consistently in route and controller layers.

**Rule**

- raise explicit `HTTPException` for expected failures
- catch and re-raise known `HTTPException`
- handle unexpected exceptions separately
- log failures before translating them into API responses

---

### 4. Prefer Guard Clauses

Invalid states should be checked early.

**Rule**

- validate authentication early
- validate authorization early
- validate missing resources early
- avoid unnecessary deep nesting

---

### 5. Separate Authentication, Authorization, and Business Logic

**Rule**

- authenticate first
- authorize second
- run business logic after access is valid

This keeps routes and controllers easier to read and maintain.

---

### 6. Log Intentionally

Logging should help with tracing and debugging.

**Rule**

- use `info` for normal flow
- use `warning` for invalid access or business-rule problems
- use `error` for failures and exceptions

Sensitive information must never be logged carelessly.

---

### 7. Keep API Errors Explicit

**Rule**

- use proper HTTP status codes
- use meaningful `detail` messages
- avoid vague error responses when a more specific one is possible

Examples:

- `401` for authentication failures
- `403` for authorization failures
- `404` for missing resources
- `500` for unexpected server errors

---

### 8. Keep API Versioning Consistent

All backend routes should use versioned prefixes such as `/v1`.

**Rule**

- keep route versioning consistent across both backends
- avoid mixing versioned and unversioned route groups

---

### 9. Keep Response Models Consistent

Use defined request and response schemas consistently.

**Rule**

- prefer response models over ad hoc dictionaries
- keep request and response contracts aligned with actual backend behavior

---

### 10. Make State Transitions Explicit

Whenever transaction, quote, payment, ticket, or policy status changes, that transition should be clear in code.

**Rule**

- update statuses intentionally
- use meaningful status names
- avoid hidden state changes

---

### 11. Prefer Readability Over Cleverness

Backend code should be easy to follow.

**Rule**

- use clear naming
- keep business flow steps explicit
- avoid unnecessarily compact logic

---

## Backend Summary

InsureFlow backend development should follow these core principles:

- two clearly separated backend services
- strict service boundaries
- secure API-key-based company communication
- transaction-based lifecycle tracking
- explicit admin security
- consistent route, controller, CRUD structure
- readable and maintainable backend code

This file should be updated whenever a backend architectural decision or backend coding standard changes.

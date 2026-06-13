---
name: firm-coding-rules
description: Use this skill whenever writing or reviewing backend code for this project so the code follows the firm's required patterns for models, schemas, CRUD, controllers, routers, logging, authentication, and error handling.
---

# Firm Coding Rules Skill

## Purpose

This skill defines the coding rules that must be followed while writing,
reviewing, or refactoring backend code in this project.

Use this skill for:

- models
- request and response schemas
- CRUD classes
- controllers
- routers
- auth-related helpers
- endpoint reviews

This skill is the reusable rulebook for backend implementation quality and
consistency.

## Core Principle

Keep code explicit, structured, logged, documented, and secure.

The codebase must prefer:

- readability over clever shortcuts
- strict layer separation
- strong typing
- documented fields and methods
- guard clauses over deep nesting
- helper-driven security logic

## Required Layer Separation

### Model Layer

The model layer is the source of truth for persisted database structure.

Rules:

- Use strongly typed ODMantic `Model` classes for collections.
- Use strongly typed `BaseModel` classes for embedded sub-models.
- Define enums explicitly with `str, Enum`.
- Add docstrings to enums, embedded models, and persisted models.
- Add field descriptions to all fields with `Field(...)`.
- Use `unique=True` where identity must be unique.
- Use `created_at` and `updated_at` with timezone-aware UTC defaults.
- Use strict model configuration with `extra="forbid"`.
- Keep security-sensitive fields explicit, such as hashed passwords and hashed OTP state.
- Do not store plain passwords.
- Do not store plain OTP values.

### Schema Layer

The schema layer is for validation and serialization only.

Rules:

- Create separate request and response schemas.
- Add class docstrings with an `Attributes` section.
- Add `description` to all schema fields.
- Use nested schemas instead of loose dictionaries when structure is known.
- Use optional fields with `None` defaults for update schemas.
- Keep schema names explicit and use-case-driven.
- Keep request and response contracts self-explanatory.
- Use timezone-aware UTC defaults only when the schema truly owns timestamp generation.

### CRUD Layer

The CRUD layer performs database operations only.

Rules:

- CRUD classes must not contain business logic.
- CRUD classes must not perform auth decisions.
- CRUD classes may create, fetch, update, list, and delete documents.
- CRUD classes may update timestamps that belong to persistence behavior.
- CRUD classes should receive or return model objects, not HTTP responses.
- CRUD classes should stay small and direct.

### Controller Layer

The controller layer contains business logic and use-case orchestration.

Rules:

- Controllers coordinate CRUD, auth helpers, utility helpers, and state changes.
- Controllers must not contain raw database queries when CRUD exists.
- Every public controller method must have a proper docstring.
- Every controller method should use structured logging.
- Every controller method should use `try/except` when it performs non-trivial flow.
- Re-raise known `HTTPException`.
- Convert unexpected exceptions into explicit server errors.
- Normalize inputs early when required, such as lowercasing emails.
- Use guard clauses for invalid state checks.
- Keep security logic helper-driven.
- Clear or roll back OTP state when business flow requires it.

### Router Layer

The router layer is only for HTTP interaction.

Rules:

- Routers define paths, methods, dependencies, request schemas, and response schemas.
- Routers must remain thin.
- Routers must not contain business logic.
- Routers call controller methods.
- Routers should transform controller output into response schemas when needed.
- Use `response_model` explicitly.
- Use versioned paths consistently, such as `/v1/...`.
- Use dependency injection for tokens, auth, and guarded routes.
- Validate auth state early in the route when required.
- Log route entry and route failures.
- Add endpoint docstrings with purpose, arguments, return value, and raised errors.

## Logging Rules

Logging is mandatory in controllers and routers.

Rules:

- Create a module-level logger once.
- Use `info` for normal flow entry and successful milestones.
- Use `warning` for invalid access, suspicious behavior, missing resources, bad credentials, or business-rule rejection.
- Use `error` for failures and unexpected exceptions.
- Log before raising translated server errors.
- Never log secrets, plain passwords, plain OTP values, or sensitive tokens.

## Docstring Rules

Docstrings are required for:

- enums
- models
- embedded models
- request schemas
- response schemas
- controller classes
- non-trivial controller methods
- routers and route handlers where practical

Docstring expectations:

- describe purpose clearly
- include `Attributes` for models and schemas
- include `Args`, `Returns`, and `Raises` for controller and route methods when useful
- keep wording precise and helpful

## Exception Handling Rules

Rules:

- Raise explicit `HTTPException` for expected failures.
- Re-raise `HTTPException` without wrapping it again.
- Catch unexpected exceptions separately.
- Convert unknown failures into `500` server errors.
- Log the original failure before returning the translated error.
- Use meaningful `detail` messages.

## Authentication and Security Rules

Rules:

- Use helper functions for password hashing and verification.
- Use helper functions for OTP generation, hashing, and verification.
- Use helper functions for JWT generation and decoding.
- Never store plain OTP values.
- Never store plain passwords.
- Exclude sensitive fields from API responses.
- Enforce OTP expiry, retry interval, max attempts, and attempt window rules.
- Clear OTP state after successful verification when required.
- Roll back OTP state if a dependent step fails, such as notification delivery.

## Input Normalization Rules

Rules:

- Normalize identity fields before lookup when applicable, such as lowercasing email.
- Strip whitespace from credentials and identifiers when appropriate.
- Validate missing resources early.
- Validate unsupported flow branches early.

## State Transition Rules

Rules:

- Status changes must be explicit in code.
- Transaction, quote, payment, ticket, and policy states must be updated intentionally.
- Avoid hidden state transitions.
- Use meaningful enum-driven statuses.
- Keep `last_login_at`, `last_active_at`, `updated_at`, and similar fields accurate when the business flow requires them.

## Response Construction Rules

Rules:

- Use response schemas instead of ad hoc dictionaries at route boundaries.
- Sanitize model output before returning it.
- Exclude sensitive fields such as passwords and OTP state.
- Convert database IDs to string form explicitly when exposing them through APIs.
- Keep response structure stable and predictable.

## Naming Rules

Rules:

- Use clear, intention-driven names.
- Use entity-plus-purpose naming for schemas, such as `UserLoginOtpRequest`.
- Use uppercase names for constants.
- Prefix private helper methods with `_`.
- Avoid vague abbreviations unless already standardized in the project.

## Timestamp Rules

Rules:

- Use timezone-aware UTC timestamps.
- Prefer `datetime.now(timezone.utc)`.
- Use `default_factory` for timestamp defaults.
- Update `updated_at` intentionally during persistence changes.

## Forbidden Patterns

Do not:

- put raw DB logic in routers
- put business logic in CRUD
- store plain OTP values
- store plain passwords
- return full model dumps with sensitive fields
- rely on undocumented magic numbers inside auth or business logic
- allow extra unplanned fields in persisted models
- create deep nesting when guard clauses are clearer
- skip logging in important controller or router flows
- skip docstrings for important classes and methods

## Review Checklist

Before finishing code, check:

- Is the correct layer doing the work?
- Are models, schemas, routers, and controllers documented?
- Is logging present and correctly leveled?
- Are auth and OTP operations helper-driven and secure?
- Are timestamps UTC-aware?
- Are response models explicit?
- Are sensitive fields excluded?
- Are state transitions explicit?
- Are exceptions handled in the standard pattern?

## Skill Usage Rule

Whenever backend code is created or reviewed for this project, apply this skill
before finalizing the implementation.

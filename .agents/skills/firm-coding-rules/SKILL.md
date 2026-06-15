---
name: firm-coding-rules
description: Use this skill whenever writing or reviewing backend code for this project so the code follows the firm's required patterns for models, schemas, CRUD, controllers, routers, logging, authentication, and error handling.
---

# Firm Coding Rules Skill

## Purpose

This skill defines the coding rules that must be followed while writing,
reviewing, or refactoring backend code in this project.

This file is the rulebook.
The companion skill `firm-backend-patterns` is the concrete pattern reference
derived from the firm's sample snippets.

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
- Every public controller and service method should use structured logging.
- Every controller and service method should use `try/except` when it performs non-trivial flow.
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

Logging is mandatory in controllers, routers, and services.

Rules:

- Create a module-level logger once.
- Use `info` for normal flow entry and successful milestones.
- Use `warning` for invalid access, suspicious behavior, missing resources, bad credentials, or business-rule rejection.
- Use `error` for failures and unexpected exceptions.
- Log before raising translated server errors.
- Never log secrets, plain passwords, plain OTP values, or sensitive tokens.

## Exception Handling Rules

Rules:

- Raise explicit `HTTPException` for expected failures.
- Re-raise `HTTPException` without wrapping it again.
- Catch unexpected exceptions separately.
- Convert unknown failures into `500` server errors.
- Log the original failure before returning the translated error.
- Use meaningful `detail` messages.

## Review Checklist

Before finishing code, check:

- Is the correct layer doing the work?
- Are models, schemas, routers, controllers, and services documented?
- Is logging present and correctly leveled?
- Are auth and OTP operations helper-driven and secure?
- Are timestamps UTC-aware?
- Are response models explicit?
- Are sensitive fields excluded?
- Are state transitions explicit?
- Are exceptions handled in the standard pattern?

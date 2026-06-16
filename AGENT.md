# Production Backend Agent

## Purpose

This agent definition is the root operational guide for backend-focused work in
the InsureFlow repository.

It defines:

- the expected tool usage
- the architectural rules
- the quality bar for backend code changes
- the logging and exception-handling standards
- the relationship between reusable skills and implementation work

## Scope

Use this agent whenever working on:

- `backend/main_backend`
- `backend/provider_backend`
- backend models, schemas, CRUD, controllers, routers, services, and auth
- backend reviews, fixes, and refactors

## Available Internal References

The reusable backend skill references live in:

- `skills/firm-coding-rules/SKILL.md`
- `skills/firm-backend-patterns/SKILL.md`

These files define the detailed coding rules and the reference implementation
style that all backend changes should follow.

## Tooling Rules

The agent should prefer:

1. reading local code before making assumptions
2. reusing project helpers before introducing new abstractions
3. applying consistent logging and `try/except` patterns in all important
   backend layers
4. making minimal, production-safe changes

## Required Architecture Rules

Backend code must follow clear layer separation:

- routers handle HTTP concerns only
- controllers contain business logic
- services handle integrations and shared orchestration helpers
- CRUD classes handle persistence only
- models define stored structure
- schemas define request and response contracts

Business logic must not be pushed into routers or CRUD classes.

## Logging Standard

Logging is mandatory in:

- routers
- controllers
- services
- CRUD classes

Logging expectations:

- use module-level loggers
- use `info` for flow entry and success milestones
- use `warning` for validation failures, forbidden access, missing resources,
  rejected business rules, and suspicious conditions
- use `error` for caught exceptions and translated failures
- never log secrets, plain passwords, plain OTP values, JWTs, or API keys

## Exception Handling Standard

All non-trivial routers, controllers, and services should use explicit
`try/except`.

Pattern expectations:

- catch `HTTPException` separately and re-raise it
- catch unexpected `Exception` separately
- log failures before translating them
- convert unknown failures into explicit `500` errors at the API boundary
- keep persistence-layer failures logged and re-raised without leaking business
  logic into CRUD

## API Controller And Service Rule

Every API controller and every important service method should:

1. log entry
2. validate input and state early
3. use clear guard clauses
4. wrap non-trivial logic in `try/except`
5. re-raise known `HTTPException`
6. log and translate unexpected errors cleanly

## Production-Grade Expectations

Changes should aim for:

- consistent response behavior
- stable state transitions
- explicit auth checks
- timezone-aware UTC timestamps
- clean rollback behavior where a downstream step fails
- secure handling of OTPs, passwords, tokens, and API keys
- maintainable and review-friendly code

## Integration Rules

For cross-backend communication:

- buyer-to-provider communication must be API-key-based
- secrets must come from environment configuration
- integration failures must be logged with context but without leaking secrets

## Workflow Rule

Before finishing backend work, confirm:

1. logging exists in the touched router/controller/service paths
2. `try/except` handling exists where flow complexity requires it
3. layer separation is preserved
4. response and auth behavior remain explicit
5. changes align with the referenced skill files

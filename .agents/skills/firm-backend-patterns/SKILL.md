# Firm Backend Reference Patterns

## Purpose

This skill is the concrete reference companion to `firm-coding-rules`.

Use it when writing or reviewing backend code so the implementation matches the
firm's real coding style, not just generic backend best practices.

## What Is Clear From The Firm Snippets

The coding style followed by the firm is very explicit and defensive.

The main patterns are:

- every important layer uses logging
- routers use explicit `try/except`
- routers raise `HTTPException` with exact `status.HTTP_*` codes
- routers validate token and role directly when the route is protected
- controllers also use explicit `try/except`
- services use logging plus explicit exception translation for integrations
- CRUD classes log and re-raise raw exceptions
- response schemas use wrapper responses like `message + data`
- schemas, models, and methods use proper docstrings
- all fields use `Field(..., description="...")`
- timestamps are UTC-aware
- OTP and password handling are strict and helper-driven

## Router Pattern

Expected router behavior:

- create a module-level logger
- define versioned routes like `/v1/...`
- document every route with a docstring
- log route entry with `logging.info(...)`
- decode and validate JWT inside protected routes when required
- check admin or role access in the route when needed
- call the controller
- catch `HTTPException` separately
- catch unexpected `Exception` separately
- convert unexpected errors to `HTTP_500_INTERNAL_SERVER_ERROR`

## Controller And Service Pattern

Expected controller and service behavior:

- create a module-level logger
- normalize inputs early
- use explicit state checks
- use `try/except HTTPException`
- use `try/except Exception`
- log every important branch
- use precise `status.HTTP_*` codes
- roll back state when a dependent action fails

## CRUD Pattern

Expected CRUD behavior:

- class-based CRUD
- module-level logger
- small direct methods only
- `try/except Exception` in methods
- log function execution
- log failures
- re-raise the original exception
- no `HTTPException` in CRUD

## Practical Use Rule

Before writing a new backend file, check:

1. Is there a matching pattern in this skill?
2. Does the code use the same logging style?
3. Does the code use the same exception style?
4. Does the controller or service avoid vague or silent failures?
5. Is the route still thin and explicit?

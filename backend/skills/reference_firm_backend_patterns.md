# Firm Backend Reference Patterns

## Purpose

This file is the concrete reference companion to `rule_skills.md`.

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
- CRUD classes log and re-raise raw exceptions
- response schemas use wrapper responses like `message + data`
- schemas, models, and methods use proper docstrings
- all fields use `Field(..., description="...")`
- `ConfigDict(extra="forbid")` is preferred in schemas and models where needed
- timestamps are UTC-aware
- OTP and password handling are strict and helper-driven

## Router Pattern

The router style is not minimalistic. It is explicit.

Expected router behavior:

- import `APIRouter`, `HTTPException`, `status`, and `Depends`
- create a module-level logger
- define versioned routes like `/v1/...`
- document every route with a docstring
- log route entry with `logging.info(...)`
- decode and validate JWT inside protected routes when required by the firm flow
- check admin or role access in the route when needed
- call the controller
- build the response schema explicitly
- return `response.model_dump()` when following the firm pattern
- catch `HTTPException` separately
- catch unexpected `Exception` separately
- convert unexpected errors to `HTTP_500_INTERNAL_SERVER_ERROR`

Canonical pattern:

```python
@router.get("/v1/users", response_model=UsersListResponse)
async def get_users(token: str = Depends(oauth2_scheme)):
    """Fetch all users."""
    try:
        logging.info("Calling /v1/users endpoint")
        authenticated_user_details = decodeJWT(token=token)
        if not authenticated_user_details:
            logging.warning("Invalid or expired token provided for fetching users")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        if authenticated_user_details.get("user_role") != "ADMIN":
            logging.warning("Unauthorized access attempt to /v1/users endpoint")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )

        result = await UserController().list_users()
        response = UsersListResponse(
            message="Users fetched successfully",
            users=[...],
        )
        return response.model_dump()
    except HTTPException as httperror:
        logging.error(f"Error in /v1/users endpoint: {httperror}")
        raise httperror
    except Exception as error:
        logging.error(f"Error in /v1/users endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )
```

## Response Schema Pattern

The firm prefers response wrappers instead of returning loose objects.

Expected response schema behavior:

- use `BaseModel`
- add class docstrings with `Attributes`
- add `Field(..., description="...")` everywhere
- use nested response schemas for structured payloads
- use wrapper response objects such as:
  - `message`
  - `data`
  - `items`
  - `users`
  - other explicit top-level keys
- use `ConfigDict(extra="forbid")` when the response should stay strict

Canonical pattern:

```python
class UserResponse(BaseModel):
    """Represents a user entry returned by user listing endpoints.

    Attributes:
        id: String representation of the persisted MongoDB user ID.
        first_name: User's given name.
        last_name: User's family name.
    """

    id: str = Field(..., description="String representation of the user ID")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")


class UsersListResponse(BaseModel):
    """Represents the API response returned after fetching all users.

    Attributes:
        message: Human-readable success message.
        users: Serialized list of user details.
    """

    message: str = Field(..., description="Success message for the request")
    users: list[UserResponse] = Field(..., description="List of user details")

    model_config = ConfigDict(extra="forbid")
```

## Controller Pattern

The firm controller style is also explicit and defensive.

Expected controller behavior:

- create a module-level logger
- define auth and OTP constants near the top when needed
- normalize inputs early
- use explicit state checks
- use `try/except HTTPException`
- use `try/except Exception`
- log every important branch
- use precise `status.HTTP_*` codes
- clear OTP after successful verification
- roll back OTP state if a dependent action fails
- return structured dictionaries or response-ready payloads when that is the firm pattern

Canonical controller traits:

- constants like:
  - `OTP_EXPIRY_SECONDS`
  - `OTP_REQUEST_INTERVAL_SECONDS`
  - `MAX_OTP_ATTEMPTS`
  - `OTP_ATTEMPT_WINDOW_SECONDS`
- validation for:
  - resend interval
  - OTP expiry
  - maximum attempts
  - attempt window reset
- sensitive output excluded from returned payloads

## CRUD Pattern

The firm CRUD style is simple and logged.

Expected CRUD behavior:

- class-based CRUD
- module-level logger
- small direct methods only
- `try/except Exception` in methods
- log function execution
- log failures
- re-raise the original exception
- no `HTTPException` in CRUD
- update `updated_at` explicitly where required

Canonical CRUD pattern:

```python
class CRUDAuth(CRUDBase[User, UserCreateRequest, UserUpdateRequest]):
    async def get_by_email(self, email: str):
        """Fetch a user document by email."""
        try:
            logging.info("Executing CRUDAuth.get_by_email function")
            return await self.engine.find_one(self.model, self.model.email == email)
        except Exception as error:
            logging.error(f"Error in CRUDAuth.get_by_email function: {error}")
            raise
```

## Logging Pattern

The firm uses logging at every important layer.

Expected logging behavior:

- `logging = logger(__name__)` at module level
- `info` for entry and success flow
- `warning` for invalid token, forbidden role, missing resource, rejected business condition
- `error` for caught exceptions
- log context like endpoint name, user id, or entity id when useful
- never log plain password, plain OTP, or secret token values

## Exception Pattern

The firm prefers very explicit exception handling.

Expected exception behavior:

- for routers:
  - `except HTTPException as httperror:`
  - log it
  - `raise httperror`
- for unexpected failures:
  - `except Exception as error:`
  - log it
  - raise `HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, ...)`
- for CRUD:
  - catch generic exception
  - log it
  - re-raise

## Authentication Pattern

Expected auth behavior:

- JWT decode is checked explicitly in protected routes
- invalid or expired token returns `401`
- wrong role returns `403`
- passwords are hashed only
- OTP is hashed only
- OTP verification enforces:
  - expiry
  - resend interval
  - max attempts
  - attempt window

## What Should Improve In Future Code

When coding next, the following must improve:

- routers must use the firm's full `try/except` structure
- routers must use exact `status.HTTP_*` constants
- routers must log route entry and failures more explicitly
- routes must build and return wrapper response schemas consistently
- controllers must align more closely with the firm's OTP and exception style
- CRUD methods must keep the same log-and-reraise pattern
- docstrings must be present in all important routes and controller methods

## Practical Use Rule

Before writing a new backend file, check:

1. Is there a matching pattern in this file?
2. Does the code use the same logging style?
3. Does the code use the same exception style?
4. Does the route return a proper wrapper response?
5. Does the controller avoid vague or silent failures?

If not, rewrite the code to match this reference.

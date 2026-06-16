"""Transaction routes for the InsureFlow main backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decodeJWT
from commons.logger import logger
from core.controllers.transaction_controller import TransactionController
from core.apis.schemas.request_schema.quote_request_schema import (
    QuoteSelectAddOnsRequest,
    QuoteSelectPlanRequest,
)
from core.apis.schemas.response_schema.transaction_response_schema import (
    TransactionListResponse,
    TransactionResponse,
)

logging = logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/login-otp/verify")
transaction_router = APIRouter(tags=["transactions"])


def _get_authenticated_user(token: str) -> dict:
    """Validate a JWT token and return its decoded payload."""

    authenticated_user_details = decodeJWT(token=token)
    if not authenticated_user_details:
        logging.warning("Invalid or expired token provided for main transaction routes")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return authenticated_user_details


def _ensure_admin_or_owner(
    authenticated_user_details: dict,
    owner_user_id: str,
    resource_name: str,
    resource_identifier: str,
) -> None:
    """Allow access only to admins or the resource owner."""

    if (
        authenticated_user_details.get("user_role") != "ADMIN"
        and authenticated_user_details.get("id") != owner_user_id
    ):
        logging.warning(
            "Unauthorized access attempt to %s %s by user ID %s",
            resource_name,
            resource_identifier,
            authenticated_user_details.get("id"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )


@transaction_router.get(
    "/v1/transactions/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_transaction(
    transaction_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TransactionResponse:
    """Fetch one transaction by business transaction id (requires auth — returning customers only)."""

    try:
        logging.info("Calling GET /v1/transactions/%s endpoint", transaction_id)
        authenticated_user_details = _get_authenticated_user(token)
        transaction_response = await TransactionController().get_transaction(transaction_id)
        _ensure_admin_or_owner(
            authenticated_user_details,
            transaction_response.user_id,
            "transaction",
            transaction_id,
        )
        return transaction_response
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/transactions/%s endpoint: %s",
            transaction_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/transactions/%s endpoint: %s",
            transaction_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transaction",
        )


@transaction_router.get(
    "/v1/users/{user_id}/transactions",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_user_transactions(
    user_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TransactionListResponse:
    """Fetch all transactions for one user (requires auth — dashboard only)."""

    try:
        logging.info("Calling GET /v1/users/%s/transactions endpoint", user_id)
        authenticated_user_details = _get_authenticated_user(token)
        if (
            authenticated_user_details.get("user_role") != "ADMIN"
            and authenticated_user_details.get("id") != user_id
        ):
            logging.warning(
                "Unauthorized access attempt to /v1/users/%s/transactions by user ID %s",
                user_id,
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await TransactionController().list_user_transactions(user_id)
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/users/%s/transactions endpoint: %s",
            user_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/users/%s/transactions endpoint: %s",
            user_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list user transactions",
        )


@transaction_router.get(
    "/v1/admins/transactions",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_all_transactions(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TransactionListResponse:
    """Return all transactions for the customer-app admin dashboard."""

    try:
        logging.info("Calling GET /v1/admins/transactions endpoint")
        authenticated_user_details = _get_authenticated_user(token)
        if authenticated_user_details.get("user_role") != "ADMIN":
            logging.warning(
                "Unauthorized access attempt to GET /v1/admins/transactions by user ID %s",
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await TransactionController().list_all_transactions()
    except HTTPException as httperror:
        logging.error("Error in GET /v1/admins/transactions endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in GET /v1/admins/transactions endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list transactions",
        )


@transaction_router.get(
    "/v1/admins/transactions/pending-forms",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_pending_forms(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TransactionListResponse:
    """Return incomplete customer journeys for the admin pending-forms view."""

    try:
        logging.info("Calling GET /v1/admins/transactions/pending-forms endpoint")
        authenticated_user_details = _get_authenticated_user(token)
        if authenticated_user_details.get("user_role") != "ADMIN":
            logging.warning(
                "Unauthorized access attempt to GET /v1/admins/transactions/pending-forms by user ID %s",
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await TransactionController().list_pending_forms()
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/admins/transactions/pending-forms endpoint: %s",
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/admins/transactions/pending-forms endpoint: %s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list pending forms",
        )


@transaction_router.get(
    "/v1/admins/transactions/completed-journeys",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_completed_journeys(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TransactionListResponse:
    """Return purchased customer journeys for the admin completed-journeys view."""

    try:
        logging.info(
            "Calling GET /v1/admins/transactions/completed-journeys endpoint"
        )
        authenticated_user_details = _get_authenticated_user(token)
        if authenticated_user_details.get("user_role") != "ADMIN":
            logging.warning(
                "Unauthorized access attempt to GET /v1/admins/transactions/completed-journeys by user ID %s",
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await TransactionController().list_completed_journeys()
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/admins/transactions/completed-journeys endpoint: %s",
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/admins/transactions/completed-journeys endpoint: %s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list completed journeys",
        )


@transaction_router.patch(
    "/v1/transactions/select-plan",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
)
async def select_plan(
    payload: QuoteSelectPlanRequest,
) -> TransactionResponse:
    """Save the selected plan on a transaction.

    No authentication required — the transaction_id UUID is unguessable
    and the customer has just come from the quote selection step.
    """

    try:
        logging.info("Calling PATCH /v1/transactions/select-plan endpoint")
        return await TransactionController().select_plan(payload)
    except HTTPException as httperror:
        logging.error(
            "Error in PATCH /v1/transactions/select-plan endpoint: %s",
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in PATCH /v1/transactions/select-plan endpoint: %s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to select transaction plan",
        )


@transaction_router.patch(
    "/v1/transactions/select-add-ons",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
)
async def save_selected_add_ons(
    payload: QuoteSelectAddOnsRequest,
) -> TransactionResponse:
    """Save selected add-ons on a transaction.

    No authentication required — secured by unguessable transaction_id UUID.
    """

    try:
        logging.info("Calling PATCH /v1/transactions/select-add-ons endpoint")
        return await TransactionController().save_selected_add_ons(payload)
    except HTTPException as httperror:
        logging.error(
            "Error in PATCH /v1/transactions/select-add-ons endpoint: %s",
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in PATCH /v1/transactions/select-add-ons endpoint: %s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save selected add-ons",
        )

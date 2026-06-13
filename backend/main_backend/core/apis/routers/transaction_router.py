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


@transaction_router.get(
    "/v1/transactions/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_transaction(
    transaction_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TransactionResponse:
    """Fetch one transaction by business transaction id.

    Args:
        transaction_id: Transaction identifier to fetch.
        token: JWT token provided in the Authorization header.

    Returns:
        Serialized transaction response.

    Raises:
        HTTPException: If token validation or lookup fails.
    """

    try:
        logging.info("Calling GET /v1/transactions/%s endpoint", transaction_id)
        _get_authenticated_user(token)
        return await TransactionController().get_transaction(transaction_id)
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
    """Fetch all transactions for one user.

    Args:
        user_id: User identifier whose transactions are requested.
        token: JWT token provided in the Authorization header.

    Returns:
        List of serialized transactions.

    Raises:
        HTTPException: If token validation or access control fails.
    """

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


@transaction_router.patch(
    "/v1/transactions/select-plan",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
)
async def select_plan(
    payload: QuoteSelectPlanRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TransactionResponse:
    """Save the selected plan on a transaction.

    Args:
        payload: Selected plan payload.
        token: JWT token provided in the Authorization header.

    Returns:
        Updated transaction response.

    Raises:
        HTTPException: If token validation or update fails.
    """

    try:
        logging.info("Calling PATCH /v1/transactions/select-plan endpoint")
        _get_authenticated_user(token)
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
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TransactionResponse:
    """Save selected add-ons on a transaction.

    Args:
        payload: Selected add-ons payload.
        token: JWT token provided in the Authorization header.

    Returns:
        Updated transaction response.

    Raises:
        HTTPException: If token validation or update fails.
    """

    try:
        logging.info("Calling PATCH /v1/transactions/select-add-ons endpoint")
        _get_authenticated_user(token)
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

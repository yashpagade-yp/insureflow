"""Quote routes for the InsureFlow main backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decodeJWT
from commons.logger import logger
from core.controllers.quote_controller import QuoteController
from core.apis.schemas.response_schema.quote_response_schema import QuoteResponse

logging = logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/login-otp/verify")
quote_router = APIRouter(tags=["quotes"])


def _get_authenticated_user(token: str) -> dict:
    """Validate a JWT token and return its decoded payload."""

    authenticated_user_details = decodeJWT(token=token)
    if not authenticated_user_details:
        logging.warning("Invalid or expired token provided for main quote routes")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return authenticated_user_details


@quote_router.get(
    "/v1/quotes/{transaction_id}",
    response_model=QuoteResponse,
    status_code=status.HTTP_200_OK,
)
async def get_quotes(
    transaction_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> QuoteResponse:
    """Fetch provider-generated quotes for one transaction."""

    try:
        logging.info("Calling GET /v1/quotes/%s endpoint", transaction_id)
        _get_authenticated_user(token)
        return await QuoteController().get_quotes(transaction_id)
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/quotes/%s endpoint: %s",
            transaction_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/quotes/%s endpoint: %s",
            transaction_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quotes",
        )

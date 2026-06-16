"""Quote routes for the InsureFlow main backend."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from commons.logger import logger
from core.controllers.quote_controller import QuoteController
from core.apis.schemas.response_schema.quote_response_schema import QuoteResponse

logging = logger(__name__)
quote_router = APIRouter(tags=["quotes"])


@quote_router.get(
    "/v1/quotes/{transaction_id}",
    response_model=QuoteResponse,
    status_code=status.HTTP_200_OK,
)
async def get_quotes(
    transaction_id: str,
) -> QuoteResponse:
    """Fetch provider-generated quotes for one transaction.

    No authentication required — the UUID transaction_id is unguessable
    and acts as a secure, one-time access token for the customer journey.
    """

    try:
        logging.info("Calling GET /v1/quotes/%s endpoint", transaction_id)
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

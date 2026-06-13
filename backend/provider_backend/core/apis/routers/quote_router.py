"""Quote-generation and quote-selection routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ....commons.logger import logger
from ...controllers.quote_controller import QuoteController
from ..schemas.request_schema.quote_request_schema import (
    QuoteGenerationRequest,
    QuoteSelectAddOnsRequest,
)
from ..schemas.response_schema.quote_response_schema import QuoteResponse

logging = logger(__name__)
router = APIRouter(prefix="/v1/quotes", tags=["quotes"])
quote_controller = QuoteController()


@router.post("/generate", response_model=QuoteResponse)
async def generate_quotes(payload: QuoteGenerationRequest) -> QuoteResponse:
    """Generate provider quote items for one transaction.

    Args:
        payload: Quote-generation payload received from the main backend.

    Returns:
        QuoteResponse: Generated provider-quote response.

    Raises:
        HTTPException: If quote generation fails.
    """

    try:
        logging.info("Calling /v1/quotes/generate endpoint")
        response = await quote_controller.generate_quotes(payload)
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/quotes/generate endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/quotes/generate endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )


@router.post("/{transaction_id}/select-plan/{selected_plan_id}", response_model=QuoteResponse)
async def select_plan(transaction_id: str, selected_plan_id: str) -> QuoteResponse:
    """Mark one provider quote item as selected for a transaction.

    Args:
        transaction_id: Transaction identifier of the quote journey.
        selected_plan_id: Provider plan identifier selected by the customer.

    Returns:
        QuoteResponse: Updated provider-quote response.

    Raises:
        HTTPException: If quote-plan selection fails.
    """

    try:
        logging.info(
            "Calling /v1/quotes/%s/select-plan/%s endpoint",
            transaction_id,
            selected_plan_id,
        )
        response = await quote_controller.select_plan(transaction_id, selected_plan_id)
        return response
    except HTTPException as httperror:
        logging.error(
            "Error in /v1/quotes/%s/select-plan/%s endpoint: %s",
            transaction_id,
            selected_plan_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in /v1/quotes/%s/select-plan/%s endpoint: %s",
            transaction_id,
            selected_plan_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )


@router.post("/{transaction_id}/select-add-ons/{selected_plan_id}", response_model=QuoteResponse)
async def save_selected_add_ons(
    transaction_id: str,
    selected_plan_id: str,
    payload: QuoteSelectAddOnsRequest,
) -> QuoteResponse:
    """Save selected add-ons for one chosen provider plan.

    Args:
        transaction_id: Transaction identifier of the quote journey.
        selected_plan_id: Provider plan identifier chosen by the customer.
        payload: Selected add-ons received for the chosen plan.

    Returns:
        QuoteResponse: Updated provider-quote response.

    Raises:
        HTTPException: If selected add-ons cannot be saved.
    """

    try:
        logging.info(
            "Calling /v1/quotes/%s/select-add-ons/%s endpoint",
            transaction_id,
            selected_plan_id,
        )
        response = await quote_controller.save_selected_add_ons(
            transaction_id=transaction_id,
            selected_plan_id=selected_plan_id,
            selected_add_ons=[
                item.model_dump() for item in payload.selected_add_ons
            ],
        )
        return response
    except HTTPException as httperror:
        logging.error(
            "Error in /v1/quotes/%s/select-add-ons/%s endpoint: %s",
            transaction_id,
            selected_plan_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in /v1/quotes/%s/select-add-ons/%s endpoint: %s",
            transaction_id,
            selected_plan_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )


@router.get("/{transaction_id}", response_model=QuoteResponse)
async def get_quote(transaction_id: str) -> QuoteResponse:
    """Return one provider quote document by transaction id.

    Args:
        transaction_id: Transaction identifier of the quote journey.

    Returns:
        QuoteResponse: Provider-quote response.

    Raises:
        HTTPException: If the quote cannot be found or returned.
    """

    try:
        logging.info("Calling /v1/quotes/%s endpoint", transaction_id)
        response = await quote_controller.get_quote(transaction_id)
        return response
    except HTTPException as httperror:
        logging.error(
            "Error in /v1/quotes/%s endpoint: %s",
            transaction_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/quotes/%s endpoint: %s", transaction_id, error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )

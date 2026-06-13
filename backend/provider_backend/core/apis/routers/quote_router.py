"""Quote-generation and quote-selection routes for the provider backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from commons.logger import logger
from core.controllers.quote_controller import QuoteController
from core.services.broker_auth_service import validate_broker_api_key
from core.apis.schemas.request_schema.quote_request_schema import (
    QuoteGenerationRequest,
    QuoteSelectAddOnsRequest,
)
from core.apis.schemas.response_schema.quote_response_schema import QuoteResponse
from core.models.company_model import CompanyModel

logging = logger(__name__)
router = APIRouter(prefix="/v1/quotes", tags=["quotes"])
quote_controller = QuoteController()


@router.post("/generate", response_model=QuoteResponse)
async def generate_quotes(
    payload: QuoteGenerationRequest,
    broker_company: Annotated[CompanyModel, Depends(validate_broker_api_key)],
) -> QuoteResponse:
    """Generate provider quote items for one transaction.

    Args:
        payload: Quote-generation payload received from the main backend.

    Returns:
        QuoteResponse: Generated provider-quote response.

    Raises:
        HTTPException: If quote generation fails.
    """

    try:
        logging.info(
            "Calling /v1/quotes/generate endpoint for broker company %s",
            broker_company.company_name,
        )
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
async def select_plan(
    transaction_id: str,
    selected_plan_id: str,
    broker_company: Annotated[CompanyModel, Depends(validate_broker_api_key)],
) -> QuoteResponse:
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
            "Calling /v1/quotes/%s/select-plan/%s endpoint for broker company %s",
            transaction_id,
            selected_plan_id,
            broker_company.company_name,
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
    broker_company: Annotated[CompanyModel, Depends(validate_broker_api_key)],
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
            "Calling /v1/quotes/%s/select-add-ons/%s endpoint for broker company %s",
            transaction_id,
            selected_plan_id,
            broker_company.company_name,
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
async def get_quote(
    transaction_id: str,
    broker_company: Annotated[CompanyModel, Depends(validate_broker_api_key)],
) -> QuoteResponse:
    """Return one provider quote document by transaction id.

    Args:
        transaction_id: Transaction identifier of the quote journey.

    Returns:
        QuoteResponse: Provider-quote response.

    Raises:
        HTTPException: If the quote cannot be found or returned.
    """

    try:
        logging.info(
            "Calling /v1/quotes/%s endpoint for broker company %s",
            transaction_id,
            broker_company.company_name,
        )
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

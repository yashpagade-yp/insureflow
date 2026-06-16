"""Quote-generation and quote-selection routes for the provider backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decodeJWT
from commons.logger import logger
from core.controllers.quote_controller import QuoteController
from core.services.broker_auth_service import validate_broker_api_key
from core.apis.schemas.request_schema.quote_request_schema import (
    QuoteGenerationRequest,
    QuoteSelectAddOnsRequest,
)
from core.apis.schemas.response_schema.quote_response_schema import (
    QuoteListResponse,
    QuoteResponse,
)
from core.models.company_model import CompanyModel

logging = logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/provider-auth/login")
router = APIRouter(prefix="/v1/quotes", tags=["quotes"])
quote_controller = QuoteController()


def _validate_provider_admin(token: str, endpoint_name: str) -> dict:
    """Validate the provider-admin JWT for protected quote routes."""

    authenticated_user_details = decodeJWT(token=token)
    if not authenticated_user_details:
        logging.warning(
            "Invalid or expired token provided for %s endpoint",
            endpoint_name,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if authenticated_user_details.get("user_role") != "ADMIN":
        logging.warning(
            "Unauthorized access attempt to %s endpoint by user ID %s",
            endpoint_name,
            authenticated_user_details.get("id"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )

    return authenticated_user_details


@router.get("", response_model=QuoteListResponse)
async def list_quotes(token: Annotated[str, Depends(oauth2_scheme)]) -> QuoteListResponse:
    """Return all provider quote records for the provider-admin dashboard.

    Args:
        token: JWT token provided in the Authorization header.

    Returns:
        QuoteListResponse: Provider quote-record list response.

    Raises:
        HTTPException: If quote listing fails.
    """

    try:
        logging.info("Calling GET /v1/quotes endpoint for provider admin")
        _validate_provider_admin(token=token, endpoint_name="/v1/quotes")
        return await quote_controller.list_quotes()
    except HTTPException as httperror:
        logging.error("Error in GET /v1/quotes endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in GET /v1/quotes endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list quote records.",
        )


@router.get("/admin/{transaction_id}", response_model=QuoteResponse)
async def get_quote_for_admin(
    transaction_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> QuoteResponse:
    """Return one provider quote record for the provider-admin dashboard.

    Args:
        transaction_id: Transaction identifier of the quote journey.
        token: JWT token provided in the Authorization header.

    Returns:
        QuoteResponse: Provider quote-record response.

    Raises:
        HTTPException: If the quote cannot be found or returned.
    """

    try:
        logging.info("Calling GET /v1/quotes/admin/%s endpoint", transaction_id)
        _validate_provider_admin(token=token, endpoint_name="/v1/quotes/admin/{transaction_id}")
        return await quote_controller.get_quote(transaction_id)
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/quotes/admin/%s endpoint: %s",
            transaction_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/quotes/admin/%s endpoint: %s",
            transaction_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quote record.",
        )


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
            detail="Failed to generate quotes.",
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
            detail="Failed to select quote plan.",
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
            detail="Failed to save selected add-ons.",
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
            detail="Failed to fetch quote.",
        )

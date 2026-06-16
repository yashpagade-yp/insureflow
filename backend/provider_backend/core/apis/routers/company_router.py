"""Company-management routes for the provider backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decodeJWT
from commons.logger import logger
from core.controllers.company_controller import CompanyController
from core.apis.schemas.request_schema.company_request_schema import (
    CompanyCreateRequest,
    CompanyUpdateRequest,
)
from core.apis.schemas.response_schema.company_response_schema import (
    CompanyCreateResponse,
    CompanyListResponse,
    CompanyResponse,
)

logging = logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/provider-auth/login")
router = APIRouter(prefix="/v1/companies", tags=["companies"])
company_controller = CompanyController()


def _validate_provider_admin(token: str, endpoint_name: str) -> dict:
    """Validate the provider-admin JWT for protected company routes."""

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


@router.post("", response_model=CompanyCreateResponse)
async def create_company(
    payload: CompanyCreateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyCreateResponse:
    """Create a provider or mediator company record.

    Args:
        payload: Company-registration payload.
        token: JWT token provided in the Authorization header.

    Returns:
        CompanyCreateResponse: Created company response with one-time API key.

    Raises:
        HTTPException: If company creation fails.
    """

    try:
        logging.info("Calling /v1/companies endpoint")
        _validate_provider_admin(token=token, endpoint_name="/v1/companies")
        response = await company_controller.create_company(payload)
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/companies endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/companies endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company.",
        )


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyListResponse:
    """Return all registered companies.

    Args:
        token: JWT token provided in the Authorization header.

    Returns:
        CompanyListResponse: Registered company list response.

    Raises:
        HTTPException: If company listing fails.
    """

    try:
        logging.info("Calling /v1/companies endpoint")
        _validate_provider_admin(token=token, endpoint_name="/v1/companies")
        response = await company_controller.list_companies()
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/companies endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/companies endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list companies.",
        )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyResponse:
    """Return one registered company by object id.

    Args:
        company_id: ODMantic object id of the requested company.
        token: JWT token provided in the Authorization header.

    Returns:
        CompanyResponse: Registered company response.

    Raises:
        HTTPException: If the company cannot be found or returned.
    """

    try:
        logging.info("Calling /v1/companies/%s endpoint", company_id)
        _validate_provider_admin(
            token=token,
            endpoint_name="/v1/companies/{company_id}",
        )
        response = await company_controller.get_company(company_id)
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/companies/%s endpoint: %s", company_id, httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/companies/%s endpoint: %s", company_id, error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch company.",
        )


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    payload: CompanyUpdateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyResponse:
    """Apply partial updates to one registered company.

    Args:
        company_id: ODMantic object id of the company to update.
        payload: Partial company-update payload.
        token: JWT token provided in the Authorization header.

    Returns:
        CompanyResponse: Updated company response.

    Raises:
        HTTPException: If the company cannot be updated.
    """

    try:
        logging.info("Calling /v1/companies/%s endpoint", company_id)
        _validate_provider_admin(
            token=token,
            endpoint_name="/v1/companies/{company_id}",
        )
        response = await company_controller.update_company(company_id, payload)
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/companies/%s endpoint: %s", company_id, httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/companies/%s endpoint: %s", company_id, error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company.",
        )

"""Buyer-company and provider-company management routes for the provider backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decodeJWT
from commons.logger import logger
from core.apis.schemas.request_schema.company_request_schema import (
    BuyerCompanyCreateRequest,
    CompanyUpdateRequest,
    ProviderCompanyCreateRequest,
)
from core.apis.schemas.response_schema.company_response_schema import (
    CompanyCreateResponse,
    CompanyListResponse,
    CompanyResponse,
    CompanyStatusResponse,
)
from core.controllers.company_controller import CompanyController

logging = logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/provider-auth/login")
router = APIRouter(tags=["companies"])
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


@router.post("/v1/buyer-companies", response_model=CompanyCreateResponse)
async def create_buyer_company(
    payload: BuyerCompanyCreateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyCreateResponse:
    """Create one buyer company and return its one-time API key."""

    try:
        logging.info("Calling POST /v1/buyer-companies endpoint")
        _validate_provider_admin(token=token, endpoint_name="/v1/buyer-companies")
        return await company_controller.create_buyer_company(payload)
    except HTTPException as httperror:
        logging.error("Error in POST /v1/buyer-companies endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in POST /v1/buyer-companies endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create buyer company.",
        )


@router.get("/v1/buyer-companies", response_model=CompanyListResponse)
async def list_buyer_companies(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyListResponse:
    """Return all registered buyer companies."""

    try:
        logging.info("Calling GET /v1/buyer-companies endpoint")
        _validate_provider_admin(token=token, endpoint_name="/v1/buyer-companies")
        return await company_controller.list_buyer_companies()
    except HTTPException as httperror:
        logging.error("Error in GET /v1/buyer-companies endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in GET /v1/buyer-companies endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list buyer companies.",
        )


@router.get("/v1/buyer-companies/{company_id}", response_model=CompanyResponse)
async def get_buyer_company(
    company_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyResponse:
    """Return one buyer company by object id."""

    try:
        logging.info("Calling GET /v1/buyer-companies/%s endpoint", company_id)
        _validate_provider_admin(
            token=token,
            endpoint_name="/v1/buyer-companies/{company_id}",
        )
        return await company_controller.get_buyer_company(company_id)
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/buyer-companies/%s endpoint: %s",
            company_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/buyer-companies/%s endpoint: %s",
            company_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch buyer company.",
        )


@router.patch("/v1/buyer-companies/{company_id}", response_model=CompanyResponse)
async def update_buyer_company(
    company_id: str,
    payload: CompanyUpdateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyResponse:
    """Apply partial updates to one buyer company."""

    try:
        logging.info("Calling PATCH /v1/buyer-companies/%s endpoint", company_id)
        _validate_provider_admin(
            token=token,
            endpoint_name="/v1/buyer-companies/{company_id}",
        )
        return await company_controller.update_buyer_company(company_id, payload)
    except HTTPException as httperror:
        logging.error(
            "Error in PATCH /v1/buyer-companies/%s endpoint: %s",
            company_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in PATCH /v1/buyer-companies/%s endpoint: %s",
            company_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update buyer company.",
        )


@router.post("/v1/provider-companies", response_model=CompanyCreateResponse)
async def create_provider_company(
    payload: ProviderCompanyCreateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyCreateResponse:
    """Create one provider insurance company."""

    try:
        logging.info("Calling POST /v1/provider-companies endpoint")
        _validate_provider_admin(token=token, endpoint_name="/v1/provider-companies")
        return await company_controller.create_provider_company(payload)
    except HTTPException as httperror:
        logging.error("Error in POST /v1/provider-companies endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in POST /v1/provider-companies endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create provider company.",
        )


@router.get("/v1/provider-companies", response_model=CompanyListResponse)
async def list_provider_companies(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyListResponse:
    """Return all registered provider companies."""

    try:
        logging.info("Calling GET /v1/provider-companies endpoint")
        _validate_provider_admin(token=token, endpoint_name="/v1/provider-companies")
        return await company_controller.list_provider_companies()
    except HTTPException as httperror:
        logging.error("Error in GET /v1/provider-companies endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in GET /v1/provider-companies endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list provider companies.",
        )


@router.get("/v1/provider-companies/{company_id}", response_model=CompanyResponse)
async def get_provider_company(
    company_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyResponse:
    """Return one provider company by object id."""

    try:
        logging.info("Calling GET /v1/provider-companies/%s endpoint", company_id)
        _validate_provider_admin(
            token=token,
            endpoint_name="/v1/provider-companies/{company_id}",
        )
        return await company_controller.get_provider_company(company_id)
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/provider-companies/%s endpoint: %s",
            company_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/provider-companies/%s endpoint: %s",
            company_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch provider company.",
        )


@router.patch("/v1/provider-companies/{company_id}", response_model=CompanyResponse)
async def update_provider_company(
    company_id: str,
    payload: CompanyUpdateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyResponse:
    """Apply partial updates to one provider company."""

    try:
        logging.info("Calling PATCH /v1/provider-companies/%s endpoint", company_id)
        _validate_provider_admin(
            token=token,
            endpoint_name="/v1/provider-companies/{company_id}",
        )
        return await company_controller.update_provider_company(company_id, payload)
    except HTTPException as httperror:
        logging.error(
            "Error in PATCH /v1/provider-companies/%s endpoint: %s",
            company_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in PATCH /v1/provider-companies/%s endpoint: %s",
            company_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update provider company.",
        )


@router.post(
    "/v1/provider-companies/{company_id}/activate",
    response_model=CompanyStatusResponse,
)
async def activate_provider_company(
    company_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyStatusResponse:
    """Activate one provider company."""

    try:
        logging.info("Calling POST /v1/provider-companies/%s/activate endpoint", company_id)
        _validate_provider_admin(
            token=token,
            endpoint_name="/v1/provider-companies/{company_id}/activate",
        )
        return await company_controller.activate_provider_company(company_id)
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/provider-companies/%s/activate endpoint: %s",
            company_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/provider-companies/%s/activate endpoint: %s",
            company_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate provider company.",
        )


@router.post(
    "/v1/provider-companies/{company_id}/deactivate",
    response_model=CompanyStatusResponse,
)
async def deactivate_provider_company(
    company_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CompanyStatusResponse:
    """Deactivate one provider company."""

    try:
        logging.info(
            "Calling POST /v1/provider-companies/%s/deactivate endpoint",
            company_id,
        )
        _validate_provider_admin(
            token=token,
            endpoint_name="/v1/provider-companies/{company_id}/deactivate",
        )
        return await company_controller.deactivate_provider_company(company_id)
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/provider-companies/%s/deactivate endpoint: %s",
            company_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/provider-companies/%s/deactivate endpoint: %s",
            company_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate provider company.",
        )

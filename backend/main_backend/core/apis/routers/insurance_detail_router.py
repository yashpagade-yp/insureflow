"""Insurance-detail routes for the InsureFlow main backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ....commons.auth import decodeJWT
from ....commons.logger import logger
from ...controllers.insurance_detail_controller import InsuranceDetailController
from ..schemas.request_schema.insurance_detail_request_schema import (
    InsuranceDetailCreateRequest,
    InsuranceDetailUpdateRequest,
)
from ..schemas.response_schema.insurance_detail_response_schema import (
    InsuranceDetailCreateResponse,
    InsuranceDetailUpdateResponse,
    LatestIncompleteInsuranceDetailResponse,
)

logging = logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/login-otp/verify")
insurance_detail_router = APIRouter(tags=["insurance-details"])


def _get_authenticated_user(token: str) -> dict:
    """Validate a JWT token and return its decoded payload."""

    authenticated_user_details = decodeJWT(token=token)
    if not authenticated_user_details:
        logging.warning(
            "Invalid or expired token provided for main insurance-detail routes"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return authenticated_user_details


@insurance_detail_router.post(
    "/v1/insurance-details",
    response_model=InsuranceDetailCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_insurance_detail_journey(
    payload: InsuranceDetailCreateRequest,
) -> InsuranceDetailCreateResponse:
    """Create a new insurance-detail journey and linked transaction.

    Args:
        payload: Insurance detail creation payload.

    Returns:
        Newly created journey response.

    Raises:
        HTTPException: If journey creation fails.
    """

    try:
        logging.info("Calling POST /v1/insurance-details endpoint")
        return await InsuranceDetailController().create_insurance_detail_journey(
            payload
        )
    except HTTPException as httperror:
        logging.error("Error in POST /v1/insurance-details endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in POST /v1/insurance-details endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create insurance detail journey",
        )


@insurance_detail_router.patch(
    "/v1/insurance-details/{transaction_id}",
    response_model=InsuranceDetailUpdateResponse,
    status_code=status.HTTP_200_OK,
)
async def update_insurance_detail(
    transaction_id: str,
    payload: InsuranceDetailUpdateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> InsuranceDetailUpdateResponse:
    """Update a transaction-linked insurance-detail snapshot.

    Args:
        transaction_id: Business transaction identifier.
        payload: Partial insurance detail updates.
        token: JWT token provided in the Authorization header.

    Returns:
        Updated insurance-detail response.

    Raises:
        HTTPException: If token validation or update fails.
    """

    try:
        logging.info("Calling PATCH /v1/insurance-details/%s endpoint", transaction_id)
        _get_authenticated_user(token)
        return await InsuranceDetailController().update_insurance_detail(
            transaction_id,
            payload,
        )
    except HTTPException as httperror:
        logging.error(
            "Error in PATCH /v1/insurance-details/%s endpoint: %s",
            transaction_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in PATCH /v1/insurance-details/%s endpoint: %s",
            transaction_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update insurance detail",
        )


@insurance_detail_router.get(
    "/v1/users/{mobile_number}/latest-incomplete-journey",
    response_model=LatestIncompleteInsuranceDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_latest_incomplete_journey(
    mobile_number: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> LatestIncompleteInsuranceDetailResponse:
    """Fetch the latest incomplete journey for a mobile number.

    Args:
        mobile_number: Customer mobile number used for journey lookup.
        token: JWT token provided in the Authorization header.

    Returns:
        Latest incomplete journey response.

    Raises:
        HTTPException: If token validation or lookup fails.
    """

    try:
        logging.info(
            "Calling GET /v1/users/%s/latest-incomplete-journey endpoint",
            mobile_number,
        )
        _get_authenticated_user(token)
        return await InsuranceDetailController().get_latest_incomplete_journey(
            mobile_number
        )
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/users/%s/latest-incomplete-journey endpoint: %s",
            mobile_number,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/users/%s/latest-incomplete-journey endpoint: %s",
            mobile_number,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch latest incomplete journey",
        )

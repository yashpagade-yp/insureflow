"""Insurance-plan routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decodeJWT
from commons.logger import logger
from core.controllers.plan_controller import PlanController
from core.apis.schemas.request_schema.plan_request_schema import (
    PlanCreateRequest,
    PlanUpdateRequest,
)
from core.apis.schemas.response_schema.plan_response_schema import (
    PlanListResponse,
    PlanResponse,
)

logging = logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/provider-auth/login")
router = APIRouter(prefix="/v1/plans", tags=["plans"])
plan_controller = PlanController()


def _validate_provider_admin(token: str, endpoint_name: str) -> dict:
    """Validate the provider-admin JWT for protected plan routes."""

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


@router.post("", response_model=PlanResponse)
async def create_plan(
    payload: PlanCreateRequest,
    token: str = Depends(oauth2_scheme),
) -> PlanResponse:
    """Create one provider insurance plan.

    Args:
        payload: Provider-plan creation payload.
        token: JWT token provided in the Authorization header.

    Returns:
        PlanResponse: Created insurance-plan response.

    Raises:
        HTTPException: If plan creation fails.
    """

    try:
        logging.info("Calling /v1/plans endpoint")
        _validate_provider_admin(token=token, endpoint_name="/v1/plans")
        response = await plan_controller.create_plan(payload)
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/plans endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/plans endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create provider insurance plan.",
        )


@router.patch("/{plan_code}", response_model=PlanResponse)
async def update_plan(
    plan_code: str,
    payload: PlanUpdateRequest,
    token: str = Depends(oauth2_scheme),
) -> PlanResponse:
    """Apply partial updates to one provider insurance plan.

    Args:
        plan_code: Provider-side plan code of the plan to update.
        payload: Partial plan-update payload.
        token: JWT token provided in the Authorization header.

    Returns:
        PlanResponse: Updated insurance-plan response.

    Raises:
        HTTPException: If plan update fails.
    """

    try:
        logging.info("Calling /v1/plans/%s endpoint", plan_code)
        _validate_provider_admin(token=token, endpoint_name="/v1/plans/{plan_code}")
        response = await plan_controller.update_plan(plan_code, payload)
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/plans/%s endpoint: %s", plan_code, httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/plans/%s endpoint: %s", plan_code, error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update provider insurance plan.",
        )


@router.get("", response_model=PlanListResponse)
async def list_plans(token: str = Depends(oauth2_scheme)) -> PlanListResponse:
    """Return all provider insurance plans.

    Args:
        token: JWT token provided in the Authorization header.

    Returns:
        PlanListResponse: Provider insurance-plan list response.

    Raises:
        HTTPException: If plan listing fails.
    """

    try:
        logging.info("Calling /v1/plans endpoint")
        _validate_provider_admin(token=token, endpoint_name="/v1/plans")
        response = await plan_controller.list_plans()
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/plans endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/plans endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list provider insurance plans.",
        )


@router.get("/{plan_code}", response_model=PlanResponse)
async def get_plan(
    plan_code: str,
    token: str = Depends(oauth2_scheme),
) -> PlanResponse:
    """Return one provider insurance plan by plan code.

    Args:
        plan_code: Provider-side plan code of the requested plan.
        token: JWT token provided in the Authorization header.

    Returns:
        PlanResponse: Provider insurance-plan response.

    Raises:
        HTTPException: If the plan cannot be found or returned.
    """

    try:
        logging.info("Calling /v1/plans/%s endpoint", plan_code)
        _validate_provider_admin(token=token, endpoint_name="/v1/plans/{plan_code}")
        response = await plan_controller.get_plan(plan_code)
        return response
    except HTTPException as httperror:
        logging.error("Error in /v1/plans/%s endpoint: %s", plan_code, httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in /v1/plans/%s endpoint: %s", plan_code, error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch provider insurance plan.",
        )

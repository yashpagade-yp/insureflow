"""Policy routes for the InsureFlow main backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decodeJWT
from commons.logger import logger
from core.controllers.policy_controller import PolicyController
from core.apis.schemas.request_schema.policy_request_schema import (
    PolicyAttachPdfRequest,
    PolicyIssueRequest,
)
from core.apis.schemas.response_schema.policy_response_schema import (
    PolicyListResponse,
    PolicyPdfResponse,
    PolicyResponse,
)

logging = logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/login-otp/verify")
policy_router = APIRouter(tags=["policies"])


def _get_authenticated_user(token: str) -> dict:
    """Validate a JWT token and return its decoded payload."""

    authenticated_user_details = decodeJWT(token=token)
    if not authenticated_user_details:
        logging.warning("Invalid or expired token provided for main policy routes")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return authenticated_user_details


@policy_router.post(
    "/v1/policies/issue",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def issue_policy(
    payload: PolicyIssueRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> PolicyResponse:
    """Issue a new policy for a completed transaction.

    Args:
        payload: Policy issuance payload.
        token: JWT token provided in the Authorization header.

    Returns:
        Newly issued policy response.

    Raises:
        HTTPException: If token validation or policy issuance fails.
    """

    try:
        logging.info("Calling POST /v1/policies/issue endpoint")
        authenticated_user_details = _get_authenticated_user(token)
        if authenticated_user_details.get("user_role") != "ADMIN":
            logging.warning(
                "Unauthorized access attempt to POST /v1/policies/issue by user ID %s",
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await PolicyController().issue_policy(
            transaction_id=payload.transaction_id,
            user_id=payload.user_id,
            company_name=payload.company_name,
            plan_name=payload.plan_name,
            coverage_amount=payload.coverage_amount,
            base_premium=payload.base_premium,
            add_ons=[item.model_dump() for item in payload.add_ons],
            add_on_total=payload.add_on_total,
            tax_amount=payload.tax_amount,
            total_premium=payload.total_premium,
            payment_reference=payload.payment_reference,
            pdf_url=payload.pdf_url,
            duration_years=payload.duration_years,
        )
    except HTTPException as httperror:
        logging.error("Error in POST /v1/policies/issue endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in POST /v1/policies/issue endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to issue policy",
        )


@policy_router.get(
    "/v1/policies/{policy_number}",
    response_model=PolicyResponse,
    status_code=status.HTTP_200_OK,
)
async def get_policy(
    policy_number: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> PolicyResponse:
    """Fetch one issued policy by policy number.

    Args:
        policy_number: Business-facing policy number.
        token: JWT token provided in the Authorization header.

    Returns:
        Serialized policy response.

    Raises:
        HTTPException: If token validation or lookup fails.
    """

    try:
        logging.info("Calling GET /v1/policies/%s endpoint", policy_number)
        _get_authenticated_user(token)
        return await PolicyController().get_policy(policy_number)
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/policies/%s endpoint: %s",
            policy_number,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/policies/%s endpoint: %s",
            policy_number,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch policy",
        )


@policy_router.get(
    "/v1/users/{user_id}/policies",
    response_model=PolicyListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_user_policies(
    user_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> PolicyListResponse:
    """Fetch all issued policies for one user.

    Args:
        user_id: User identifier whose policies are requested.
        token: JWT token provided in the Authorization header.

    Returns:
        List of serialized policy responses.

    Raises:
        HTTPException: If token validation or access control fails.
    """

    try:
        logging.info("Calling GET /v1/users/%s/policies endpoint", user_id)
        authenticated_user_details = _get_authenticated_user(token)
        if (
            authenticated_user_details.get("user_role") != "ADMIN"
            and authenticated_user_details.get("id") != user_id
        ):
            logging.warning(
                "Unauthorized access attempt to /v1/users/%s/policies by user ID %s",
                user_id,
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await PolicyController().list_user_policies(user_id)
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/users/%s/policies endpoint: %s",
            user_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/users/%s/policies endpoint: %s",
            user_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list user policies",
        )


@policy_router.patch(
    "/v1/policies/{policy_number}/pdf",
    response_model=PolicyPdfResponse,
    status_code=status.HTTP_200_OK,
)
async def attach_policy_pdf(
    policy_number: str,
    payload: PolicyAttachPdfRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> PolicyPdfResponse:
    """Attach a generated PDF URL to a policy.

    Args:
        policy_number: Business-facing policy number.
        payload: Generated policy PDF URL payload.
        token: JWT token provided in the Authorization header.

    Returns:
        Policy PDF response.

    Raises:
        HTTPException: If token validation or update fails.
    """

    try:
        logging.info("Calling PATCH /v1/policies/%s/pdf endpoint", policy_number)
        authenticated_user_details = _get_authenticated_user(token)
        if authenticated_user_details.get("user_role") != "ADMIN":
            logging.warning(
                "Unauthorized access attempt to PATCH /v1/policies/%s/pdf by user ID %s",
                policy_number,
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await PolicyController().attach_policy_pdf(
            policy_number,
            payload.pdf_url,
        )
    except HTTPException as httperror:
        logging.error(
            "Error in PATCH /v1/policies/%s/pdf endpoint: %s",
            policy_number,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in PATCH /v1/policies/%s/pdf endpoint: %s",
            policy_number,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to attach policy PDF",
        )

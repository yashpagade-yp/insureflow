"""Support-ticket routes for the InsureFlow main backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decodeJWT
from commons.logger import logger
from core.apis.schemas.request_schema.ticket_request_schema import (
    TicketAdminResponseRequest,
    TicketCreateRequest,
    TicketUpdateRequest,
)
from core.apis.schemas.response_schema.ticket_response_schema import (
    TicketListResponse,
    TicketResponse,
)
from core.controllers.ticket_controller import TicketController

logging = logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/login-otp/verify")
ticket_router = APIRouter(tags=["tickets"])


def _get_authenticated_user(token: str) -> dict:
    """Validate a JWT token and return its decoded payload."""

    authenticated_user_details = decodeJWT(token=token)
    if not authenticated_user_details:
        logging.warning("Invalid or expired token provided for main ticket routes")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return authenticated_user_details


@ticket_router.post(
    "/v1/users/{user_id}/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    user_id: str,
    payload: TicketCreateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TicketResponse:
    """Create a support ticket for a customer's transaction.

    Args:
        user_id: User identifier creating the support ticket.
        payload: Ticket creation payload for the related transaction.
        token: JWT token provided in the Authorization header.

    Returns:
        TicketResponse: Created support-ticket response.

    Raises:
        HTTPException: If the token is invalid or access is not allowed.
    """

    try:
        logging.info("Calling POST /v1/users/%s/tickets endpoint", user_id)
        authenticated_user_details = _get_authenticated_user(token)
        if (
            authenticated_user_details.get("user_role") != "ADMIN"
            and authenticated_user_details.get("id") != user_id
        ):
            logging.warning(
                "Unauthorized ticket creation attempt for user %s by user ID %s",
                user_id,
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create a ticket for this user.",
            )
        return await TicketController().create_ticket(user_id, payload)
    except HTTPException as httperror:
        logging.error("Error in POST /v1/users/%s/tickets endpoint: %s", user_id, httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in POST /v1/users/%s/tickets endpoint: %s", user_id, error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create support ticket",
        )


@ticket_router.get(
    "/v1/users/{user_id}/tickets",
    response_model=TicketListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_user_tickets(
    user_id: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TicketListResponse:
    """Return all support tickets for a customer or admin view.

    Args:
        user_id: User identifier whose tickets should be returned.
        token: JWT token provided in the Authorization header.

    Returns:
        TicketListResponse: Ordered list of tickets for the user.

    Raises:
        HTTPException: If the token is invalid or access is not allowed.
    """

    try:
        logging.info("Calling GET /v1/users/%s/tickets endpoint", user_id)
        authenticated_user_details = _get_authenticated_user(token)
        if (
            authenticated_user_details.get("user_role") != "ADMIN"
            and authenticated_user_details.get("id") != user_id
        ):
            logging.warning(
                "Unauthorized ticket listing attempt for user %s by user ID %s",
                user_id,
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access these tickets.",
            )
        return await TicketController().list_user_tickets(user_id)
    except HTTPException as httperror:
        logging.error("Error in GET /v1/users/%s/tickets endpoint: %s", user_id, httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in GET /v1/users/%s/tickets endpoint: %s", user_id, error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list support tickets",
        )


@ticket_router.patch(
    "/v1/users/{user_id}/tickets/{ticket_id}",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
)
async def update_user_ticket(
    user_id: str,
    ticket_id: str,
    payload: TicketUpdateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TicketResponse:
    """Allow a customer to update one of their open support tickets.

    Args:
        user_id: User identifier who owns the ticket.
        ticket_id: Business ticket identifier to update.
        payload: Partial ticket updates from the customer.
        token: JWT token provided in the Authorization header.

    Returns:
        TicketResponse: Updated support-ticket response.

    Raises:
        HTTPException: If the token is invalid or access is not allowed.
    """

    try:
        logging.info(
            "Calling PATCH /v1/users/%s/tickets/%s endpoint",
            user_id,
            ticket_id,
        )
        authenticated_user_details = _get_authenticated_user(token)
        if (
            authenticated_user_details.get("user_role") != "ADMIN"
            and authenticated_user_details.get("id") != user_id
        ):
            logging.warning(
                "Unauthorized ticket update attempt for user %s by user ID %s",
                user_id,
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this ticket.",
            )
        return await TicketController().update_user_ticket(user_id, ticket_id, payload)
    except HTTPException as httperror:
        logging.error(
            "Error in PATCH /v1/users/%s/tickets/%s endpoint: %s",
            user_id,
            ticket_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in PATCH /v1/users/%s/tickets/%s endpoint: %s",
            user_id,
            ticket_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update support ticket",
        )


@ticket_router.get(
    "/v1/admins/tickets",
    response_model=TicketListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_all_tickets(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TicketListResponse:
    """Return all support tickets for the customer-app admin dashboard.

    Args:
        token: JWT token provided in the Authorization header.

    Returns:
        TicketListResponse: Ordered list of all support tickets.

    Raises:
        HTTPException: If the token is invalid or the caller is not an admin.
    """

    try:
        logging.info("Calling GET /v1/admins/tickets endpoint")
        authenticated_user_details = _get_authenticated_user(token)
        if authenticated_user_details.get("user_role") != "ADMIN":
            logging.warning(
                "Unauthorized ticket admin-list attempt by user ID %s",
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await TicketController().list_all_tickets()
    except HTTPException as httperror:
        logging.error("Error in GET /v1/admins/tickets endpoint: %s", httperror)
        raise httperror
    except Exception as error:
        logging.error("Error in GET /v1/admins/tickets endpoint: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list support tickets",
        )


@ticket_router.patch(
    "/v1/admins/tickets/{ticket_id}",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
)
async def respond_to_ticket(
    ticket_id: str,
    payload: TicketAdminResponseRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TicketResponse:
    """Allow a customer-app admin to investigate and resolve a support ticket.

    Args:
        ticket_id: Business ticket identifier to update.
        payload: Admin response payload containing the next ticket status.
        token: JWT token provided in the Authorization header.

    Returns:
        TicketResponse: Updated support-ticket response.

    Raises:
        HTTPException: If the token is invalid or the caller is not an admin.
    """

    try:
        logging.info("Calling PATCH /v1/admins/tickets/%s endpoint", ticket_id)
        authenticated_user_details = _get_authenticated_user(token)
        if authenticated_user_details.get("user_role") != "ADMIN":
            logging.warning(
                "Unauthorized ticket admin-update attempt by user ID %s",
                authenticated_user_details.get("id"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return await TicketController().respond_to_ticket(
            authenticated_user_details.get("id", ""),
            ticket_id,
            payload,
        )
    except HTTPException as httperror:
        logging.error(
            "Error in PATCH /v1/admins/tickets/%s endpoint: %s",
            ticket_id,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in PATCH /v1/admins/tickets/%s endpoint: %s",
            ticket_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update support ticket",
        )

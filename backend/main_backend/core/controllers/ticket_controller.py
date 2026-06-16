"""Controller logic for support-ticket flows in the main backend."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status

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
from core.cruds.ticket_crud import TicketCrud
from core.cruds.transaction_crud import TransactionCrud
from core.cruds.user_crud import UserCrud
from core.models.ticket_model import TicketModel, TicketStatus

logging = logger(__name__)


class TicketController:
    """Handles customer-ticket creation, listing, and admin resolution flows."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependencies."""

        self.ticket_crud = TicketCrud()
        self.user_crud = UserCrud()
        self.transaction_crud = TransactionCrud()

    async def create_ticket(
        self,
        user_id: str,
        payload: TicketCreateRequest,
    ) -> TicketResponse:
        """Create a support ticket for a user's transaction.

        Args:
            user_id: User identifier creating the ticket.
            payload: Ticket creation payload for the related transaction.

        Returns:
            TicketResponse: Created support-ticket response.

        Raises:
            HTTPException: If the user or transaction is invalid, or the ticket
                cannot be created.
        """

        try:
            logging.info("Executing TicketController.create_ticket function")
            normalized_user_id = user_id.strip()
            normalized_transaction_id = payload.transaction_id.strip()
            normalized_issue_type = payload.issue_type.strip()
            normalized_description = payload.description.strip()
            if (
                not normalized_user_id
                or not normalized_transaction_id
                or not normalized_issue_type
                or not normalized_description
            ):
                logging.warning("Ticket creation received empty required values")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User id, transaction id, issue type, and description are required.",
                )

            user = await self.user_crud.get_by_id(normalized_user_id)
            if user is None:
                logging.warning("User not found for id %s during ticket creation", normalized_user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )

            transaction = await self.transaction_crud.get_by_transaction_id(
                normalized_transaction_id
            )
            if transaction is None or transaction.user_id != normalized_user_id:
                logging.warning(
                    "Transaction %s not found for user %s during ticket creation",
                    normalized_transaction_id,
                    normalized_user_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found for this user.",
                )

            ticket = await self.ticket_crud.create(
                TicketModel.model_validate(
                    {
                        "user_id": normalized_user_id,
                        "transaction_id": normalized_transaction_id,
                        "issue_type": normalized_issue_type,
                        "description": normalized_description,
                    }
                )
            )
            logging.info(
                "Support ticket %s created successfully for user %s",
                ticket.ticket_id,
                normalized_user_id,
            )
            return self._build_response(ticket)
        except HTTPException as httperror:
            logging.error("Error in TicketController.create_ticket function: %s", httperror)
            raise httperror
        except Exception as error:
            logging.error("Error in TicketController.create_ticket function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create support ticket.",
            )

    async def list_user_tickets(self, user_id: str) -> TicketListResponse:
        """Return all support tickets for one user.

        Args:
            user_id: User identifier whose support tickets should be returned.

        Returns:
            TicketListResponse: Ordered list of support tickets for the user.

        Raises:
            HTTPException: If the user identifier is invalid or the user does
                not exist.
        """

        try:
            logging.info("Executing TicketController.list_user_tickets function")
            normalized_user_id = user_id.strip()
            if not normalized_user_id:
                logging.warning("Empty user_id provided for ticket listing")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User id is required.",
                )

            user = await self.user_crud.get_by_id(normalized_user_id)
            if user is None:
                logging.warning("User not found for id %s during ticket listing", normalized_user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )

            tickets = await self.ticket_crud.list_by_user_id(normalized_user_id)
            return TicketListResponse(
                items=[self._build_response(item) for item in tickets],
                total_count=len(tickets),
            )
        except HTTPException as httperror:
            logging.error("Error in TicketController.list_user_tickets function: %s", httperror)
            raise httperror
        except Exception as error:
            logging.error("Error in TicketController.list_user_tickets function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list support tickets.",
            )

    async def update_user_ticket(
        self,
        user_id: str,
        ticket_id: str,
        payload: TicketUpdateRequest,
    ) -> TicketResponse:
        """Allow a customer to update an open support ticket.

        Args:
            user_id: User identifier who owns the ticket.
            ticket_id: Business ticket identifier to update.
            payload: Partial user-side ticket updates.

        Returns:
            TicketResponse: Updated support-ticket response.

        Raises:
            HTTPException: If the ticket cannot be found, does not belong to the
                user, or can no longer be edited.
        """

        try:
            logging.info("Executing TicketController.update_user_ticket function")
            normalized_user_id = user_id.strip()
            normalized_ticket_id = ticket_id.strip()
            if not normalized_user_id or not normalized_ticket_id:
                logging.warning("Ticket update received empty identifiers")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User id and ticket id are required.",
                )

            ticket = await self.ticket_crud.get_by_ticket_id(normalized_ticket_id)
            if ticket is None or ticket.user_id != normalized_user_id:
                logging.warning(
                    "Ticket %s not found for user %s during ticket update",
                    normalized_ticket_id,
                    normalized_user_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ticket not found for this user.",
                )

            if ticket.ticket_status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
                logging.warning(
                    "Ticket %s cannot be edited because status is %s",
                    normalized_ticket_id,
                    ticket.ticket_status.value,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Resolved or closed tickets cannot be updated by the customer.",
                )

            updates = payload.model_dump(exclude_unset=True)
            if "issue_type" in updates and updates["issue_type"] is not None:
                updates["issue_type"] = updates["issue_type"].strip()
            if "description" in updates and updates["description"] is not None:
                updates["description"] = updates["description"].strip()
            updates = {
                field_name: field_value
                for field_name, field_value in updates.items()
                if field_value not in ("", None)
            }
            if not updates:
                logging.warning("No valid ticket updates provided for ticket %s", normalized_ticket_id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one valid ticket field must be provided.",
                )

            updated_ticket = await self.ticket_crud.update(ticket, updates)
            logging.info("Ticket %s updated successfully by user %s", normalized_ticket_id, normalized_user_id)
            return self._build_response(updated_ticket)
        except HTTPException as httperror:
            logging.error("Error in TicketController.update_user_ticket function: %s", httperror)
            raise httperror
        except Exception as error:
            logging.error("Error in TicketController.update_user_ticket function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update support ticket.",
            )

    async def list_all_tickets(self) -> TicketListResponse:
        """Return all support tickets for the customer-app admin view.

        Returns:
            TicketListResponse: Ordered list of all support tickets.

        Raises:
            HTTPException: If ticket listing fails.
        """

        try:
            logging.info("Executing TicketController.list_all_tickets function")
            tickets = await self.ticket_crud.list_all()
            return TicketListResponse(
                items=[self._build_response(item) for item in tickets],
                total_count=len(tickets),
            )
        except HTTPException as httperror:
            logging.error("Error in TicketController.list_all_tickets function: %s", httperror)
            raise httperror
        except Exception as error:
            logging.error("Error in TicketController.list_all_tickets function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list support tickets.",
            )

    async def respond_to_ticket(
        self,
        admin_id: str,
        ticket_id: str,
        payload: TicketAdminResponseRequest,
    ) -> TicketResponse:
        """Allow a customer-app admin to investigate and resolve a ticket.

        Args:
            admin_id: Admin identifier handling the ticket.
            ticket_id: Business ticket identifier to update.
            payload: Admin response message and target ticket status.

        Returns:
            TicketResponse: Updated support-ticket response.

        Raises:
            HTTPException: If the ticket cannot be found or the requested status
                transition is invalid.
        """

        try:
            logging.info("Executing TicketController.respond_to_ticket function")
            normalized_admin_id = admin_id.strip()
            normalized_ticket_id = ticket_id.strip()
            normalized_admin_response = payload.admin_response.strip()
            normalized_ticket_status = payload.ticket_status.strip().upper()
            if (
                not normalized_admin_id
                or not normalized_ticket_id
                or not normalized_admin_response
                or not normalized_ticket_status
            ):
                logging.warning("Admin ticket response received empty required values")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Admin id, ticket id, ticket status, and admin response are required.",
                )

            ticket = await self.ticket_crud.get_by_ticket_id(normalized_ticket_id)
            if ticket is None:
                logging.warning("Ticket %s not found during admin response", normalized_ticket_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ticket not found.",
                )

            try:
                ticket_status = TicketStatus(normalized_ticket_status)
            except ValueError as error:
                logging.warning("Invalid ticket status provided: %s", error)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid ticket status.",
                ) from error

            updates: dict[str, object] = {
                "admin_id": normalized_admin_id,
                "admin_response": normalized_admin_response,
                "ticket_status": ticket_status,
            }
            if ticket_status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
                updates["resolved_at"] = datetime.now(timezone.utc)

            updated_ticket = await self.ticket_crud.update(ticket, updates)
            logging.info(
                "Ticket %s updated successfully by admin %s",
                normalized_ticket_id,
                normalized_admin_id,
            )
            return self._build_response(updated_ticket)
        except HTTPException as httperror:
            logging.error("Error in TicketController.respond_to_ticket function: %s", httperror)
            raise httperror
        except Exception as error:
            logging.error("Error in TicketController.respond_to_ticket function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update support ticket.",
            )

    def _build_response(self, ticket: TicketModel) -> TicketResponse:
        """Convert a support-ticket document into the public response schema."""

        return TicketResponse(
            ticket_id=ticket.ticket_id,
            user_id=ticket.user_id,
            transaction_id=ticket.transaction_id,
            issue_type=ticket.issue_type,
            description=ticket.description,
            ticket_status=ticket.ticket_status.value,
            admin_id=ticket.admin_id,
            admin_response=ticket.admin_response,
            resolved_at=ticket.resolved_at,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        )

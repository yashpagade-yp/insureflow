"""Controller logic for provider-quote retrieval in the main backend."""

from __future__ import annotations

from fastapi import HTTPException, status

from commons.logger import logger
from core.apis.schemas.response_schema.quote_response_schema import (
    QuoteAvailableAddOnResponse,
    QuoteItemResponse,
    QuoteResponse,
    QuoteSelectedAddOnResponse,
)
from core.services.provider_service import ProviderService

logging = logger(__name__)


class QuoteController:
    """Handles provider-quote retrieval through the main backend."""

    def __init__(self) -> None:
        """Initialise the controller with its service dependency."""

        self.provider_service = ProviderService()

    async def get_quotes(self, transaction_id: str) -> QuoteResponse:
        """Fetch provider-generated quotes for one transaction.

        Args:
            transaction_id: Business transaction identifier for the quote journey.

        Returns:
            QuoteResponse: Provider-generated quotes mapped into the main-backend
                response schema.

        Raises:
            HTTPException: If the transaction identifier is invalid or the
                provider quotes cannot be fetched.
        """

        try:
            logging.info("Executing QuoteController.get_quotes function")
            normalized_transaction_id = transaction_id.strip()
            if not normalized_transaction_id:
                logging.warning("Empty transaction_id provided for quote retrieval")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction id is required.",
                )

            provider_response = await self.provider_service.get_quotes(
                normalized_transaction_id
            )
            return self._build_quote_response(provider_response)
        except HTTPException as httperror:
            logging.error("Error in QuoteController.get_quotes function: %s", httperror)
            raise httperror
        except Exception as error:
            logging.error("Error in QuoteController.get_quotes function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch quotes.",
            )

    def _build_quote_response(self, payload: dict) -> QuoteResponse:
        """Convert provider quote payload into the main-backend response schema."""

        return QuoteResponse(
            transaction_id=payload["transaction_id"],
            selected_plan_id=payload.get("selected_plan_id"),
            items=[
                QuoteItemResponse(
                    plan_id=item["plan_id"],
                    company_name=item["company_name"],
                    logo_url=item.get("logo_url"),
                    plan_name=item["plan_name"],
                    coverage_amount=item["coverage_amount"],
                    base_premium=item["base_premium"],
                    duration_years=item["duration_years"],
                    benefits=item.get("benefits", []),
                    available_add_ons=[
                        QuoteAvailableAddOnResponse(
                            name=add_on["name"],
                            description=add_on["description"],
                            price=add_on["price"],
                        )
                        for add_on in item.get("available_add_ons", [])
                    ],
                    selected_add_ons=[
                        QuoteSelectedAddOnResponse(
                            name=add_on["name"],
                            price=add_on["price"],
                        )
                        for add_on in item.get("selected_add_ons", [])
                    ],
                    add_on_total=item["add_on_total"],
                    tax_amount=item["tax_amount"],
                    total_premium=item["total_premium"],
                    quote_status=item["quote_status"],
                )
                for item in payload.get("items", [])
            ],
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
        )

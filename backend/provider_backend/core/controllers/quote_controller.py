"""Controller logic for quote generation and quote updates in provider backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from ...commons.logger import logger
from ..apis.schemas.request_schema.quote_request_schema import QuoteGenerationRequest
from ..apis.schemas.response_schema.quote_response_schema import (
    QuoteAvailableAddOnResponse,
    QuoteItemResponse,
    QuoteResponse,
    QuoteSelectedAddOnResponse,
)
from ..cruds.insurance_plan_crud import InsurancePlanCrud
from ..cruds.quote_crud import QuoteCrud
from ..models.insurance_model import InsuranceType
from ..models.quote_model import (
    AvailableAddOn,
    QuoteItem,
    QuoteModel,
    QuoteStatus,
    SelectedAddOn,
)

logging = logger(__name__)


class QuoteController:
    """Handles provider quote generation and selection business logic."""

    TAX_RATE = 0.18

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependencies."""

        self.plan_crud = InsurancePlanCrud()
        self.quote_crud = QuoteCrud()

    async def generate_quotes(self, payload: QuoteGenerationRequest) -> QuoteResponse:
        """Generate or replace the provider quote document for one transaction."""
        try:
            logging.info("Executing QuoteController.generate_quotes function")
            insurance_type = InsuranceType(payload.insurance_type)
            plans = await self.plan_crud.list_by_insurance_type(insurance_type)
            if not plans:
                logging.warning(
                    "No plans found for insurance type %s", payload.insurance_type
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No plans found for the requested insurance type.",
                )

            items = []
            for plan in plans:
                tax_amount = round(plan.base_premium * self.TAX_RATE, 2)
                total_premium = round(plan.base_premium + tax_amount, 2)
                items.append(
                    QuoteItem(
                        plan_id=str(plan.id),
                        company_name=plan.company_name,
                        logo_url=plan.logo_url,
                        plan_name=plan.plan_name,
                        coverage_amount=plan.coverage_amount,
                        base_premium=plan.base_premium,
                        duration_years=plan.duration_years,
                        benefits=plan.benefits,
                        available_add_ons=[
                            AvailableAddOn(
                                name=add_on.name,
                                description=add_on.description,
                                price=add_on.price,
                            )
                            for add_on in plan.available_add_ons
                        ],
                        selected_add_ons=[],
                        add_on_total=0.0,
                        tax_amount=tax_amount,
                        total_premium=total_premium,
                        quote_status=QuoteStatus.GENERATED,
                    )
                )

            quote = await self.quote_crud.get_by_transaction_id(payload.transaction_id)
            if quote is None:
                quote = await self.quote_crud.create(
                    QuoteModel.model_validate(
                        {
                            "transaction_id": payload.transaction_id,
                            "items": items,
                        }
                    )
                )
            else:
                quote = await self.quote_crud.replace_items(quote, items)

            logging.info(
                "Quotes generated successfully for transaction %s",
                payload.transaction_id,
            )
            return self._build_quote_response(quote)
        except HTTPException as httperror:
            logging.error(
                "Error in QuoteController.generate_quotes function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in QuoteController.generate_quotes function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate quotes.",
            )

    async def select_plan(self, transaction_id: str, selected_plan_id: str) -> QuoteResponse:
        """Mark one plan as selected inside the provider quote document."""
        try:
            logging.info("Executing QuoteController.select_plan function")
            quote = await self.quote_crud.get_by_transaction_id(transaction_id)
            if quote is None:
                logging.warning(
                    "Quote not found for transaction %s during plan selection",
                    transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Quote not found for this transaction.",
                )

            quote = await self.quote_crud.set_selected_plan_id(quote, selected_plan_id)
            for item in quote.items:
                item.quote_status = (
                    QuoteStatus.SELECTED
                    if item.plan_id == selected_plan_id
                    else QuoteStatus.GENERATED
                )

            quote.updated_at = datetime.now(timezone.utc)
            quote = await self.quote_crud.save(quote)
            logging.info(
                "Plan %s selected successfully for transaction %s",
                selected_plan_id,
                transaction_id,
            )
            return self._build_quote_response(quote)
        except HTTPException as httperror:
            logging.error(
                "Error in QuoteController.select_plan function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in QuoteController.select_plan function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to select quote plan.",
            )

    async def save_selected_add_ons(
        self,
        transaction_id: str,
        selected_plan_id: str,
        selected_add_ons: list[dict[str, Any]],
    ) -> QuoteResponse:
        """Save selected add-ons and recompute totals for the chosen quote item."""
        try:
            logging.info("Executing QuoteController.save_selected_add_ons function")
            quote = await self.quote_crud.get_by_transaction_id(transaction_id)
            if quote is None:
                logging.warning(
                    "Quote not found for transaction %s during add-on selection",
                    transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Quote not found for this transaction.",
                )

            target_item = next(
                (item for item in quote.items if item.plan_id == selected_plan_id),
                None,
            )
            if target_item is None:
                logging.warning(
                    "Selected plan %s not found in quote items for transaction %s",
                    selected_plan_id,
                    transaction_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Selected plan not found in quote items.",
                )

            selected_add_on_models = self._build_selected_add_on_models(
                selected_add_ons=selected_add_ons,
                available_add_ons=target_item.available_add_ons,
            )
            add_on_total = round(sum(item.price for item in selected_add_on_models), 2)
            subtotal = target_item.base_premium + add_on_total
            tax_amount = round(subtotal * self.TAX_RATE, 2)
            total_premium = round(subtotal + tax_amount, 2)

            quote = await self.quote_crud.set_selected_add_ons(
                quote=quote,
                plan_id=selected_plan_id,
                selected_add_ons=selected_add_on_models,
                add_on_total=add_on_total,
                tax_amount=tax_amount,
                total_premium=total_premium,
            )
            quote = await self.quote_crud.update_item_status(
                quote,
                selected_plan_id,
                QuoteStatus.CONFIRMED,
            )
            logging.info(
                "Add-ons saved successfully for plan %s and transaction %s",
                selected_plan_id,
                transaction_id,
            )
            return self._build_quote_response(quote)
        except HTTPException as httperror:
            logging.error(
                "Error in QuoteController.save_selected_add_ons function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in QuoteController.save_selected_add_ons function: %s", error
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save selected add-ons.",
            )

    async def get_quote(self, transaction_id: str) -> QuoteResponse:
        """Return one provider quote document by transaction id."""
        try:
            logging.info("Executing QuoteController.get_quote function")
            quote = await self.quote_crud.get_by_transaction_id(transaction_id)
            if quote is None:
                logging.warning(
                    "Quote not found for transaction %s", transaction_id
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Quote not found for this transaction.",
                )
            return self._build_quote_response(quote)
        except HTTPException as httperror:
            logging.error(
                "Error in QuoteController.get_quote function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in QuoteController.get_quote function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch quote.",
            )

    def _build_quote_response(self, quote: QuoteModel) -> QuoteResponse:
        """Convert a quote document into the public response schema."""

        return QuoteResponse(
            transaction_id=quote.transaction_id,
            selected_plan_id=quote.selected_plan_id,
            items=[
                QuoteItemResponse(
                    plan_id=item.plan_id,
                    company_name=item.company_name,
                    logo_url=item.logo_url,
                    plan_name=item.plan_name,
                    coverage_amount=item.coverage_amount,
                    base_premium=item.base_premium,
                    duration_years=item.duration_years,
                    benefits=item.benefits,
                    available_add_ons=[
                        QuoteAvailableAddOnResponse(
                            name=add_on.name,
                            description=add_on.description,
                            price=add_on.price,
                        )
                        for add_on in item.available_add_ons
                    ],
                    selected_add_ons=[
                        QuoteSelectedAddOnResponse(name=add_on.name, price=add_on.price)
                        for add_on in item.selected_add_ons
                    ],
                    add_on_total=item.add_on_total,
                    tax_amount=item.tax_amount,
                    total_premium=item.total_premium,
                    quote_status=item.quote_status.value,
                )
                for item in quote.items
            ],
            created_at=quote.created_at,
            updated_at=quote.updated_at,
        )

    def _build_selected_add_on_models(
        self,
        selected_add_ons: list[dict[str, Any]],
        available_add_ons: list[AvailableAddOn],
    ) -> list[SelectedAddOn]:
        """Validate and normalize selected add-ons against the quoted plan.

        Args:
            selected_add_ons: Raw selected add-ons received from the caller.
            available_add_ons: Add-ons available for the selected quote item.

        Returns:
            Normalized selected add-on models that can be stored in the quote.

        Raises:
            HTTPException: If any selected add-on does not belong to the quoted
                plan or does not match the provider-side configured price.
        """

        available_by_name = {add_on.name: add_on for add_on in available_add_ons}
        normalized_selected_add_ons: list[SelectedAddOn] = []

        for raw_add_on in selected_add_ons:
            selected_add_on = SelectedAddOn.model_validate(raw_add_on)
            matching_add_on = available_by_name.get(selected_add_on.name)
            if matching_add_on is None:
                logging.warning(
                    "Selected add-on %s is not available for the chosen plan",
                    selected_add_on.name,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Selected add-on '{selected_add_on.name}' is not available for this plan.",
                )
            if selected_add_on.price != matching_add_on.price:
                logging.warning(
                    "Selected add-on %s price mismatch. Expected %s, got %s",
                    selected_add_on.name,
                    matching_add_on.price,
                    selected_add_on.price,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Selected add-on '{selected_add_on.name}' has an invalid price.",
                )
            normalized_selected_add_ons.append(selected_add_on)

        return normalized_selected_add_ons

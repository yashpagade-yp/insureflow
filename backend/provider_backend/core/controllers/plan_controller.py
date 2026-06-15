"""Controller logic for insurance-plan flows in the provider backend."""

from __future__ import annotations

from fastapi import HTTPException, status

from commons.logger import logger
from core.apis.schemas.request_schema.plan_request_schema import (
    PlanAddOnRequest,
    PlanCreateRequest,
    PlanUpdateRequest,
)
from core.apis.schemas.response_schema.plan_response_schema import (
    PlanAddOnResponse,
    PlanListResponse,
    PlanResponse,
)
from core.cruds.insurance_plan_crud import InsurancePlanCrud
from core.models.insurance_model import EmbeddedAddOn, InsuranceModel, InsuranceType

logging = logger(__name__)


class PlanController:
    """Handles provider insurance-plan business logic."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependency."""

        self.plan_crud = InsurancePlanCrud()

    async def create_plan(self, payload: PlanCreateRequest) -> PlanResponse:
        """Create a new provider insurance plan.

        Args:
            payload: Provider-plan creation payload.

        Returns:
            PlanResponse: Created provider insurance-plan response.

        Raises:
            HTTPException: If required values are invalid, the plan already
                exists, or the plan cannot be created.
        """
        try:
            logging.info("Executing PlanController.create_plan function")
            normalized_plan_code = payload.plan_code.strip()
            normalized_company_name = payload.company_name.strip()
            normalized_plan_name = payload.plan_name.strip()
            if (
                not normalized_plan_code
                or not normalized_company_name
                or not normalized_plan_name
            ):
                logging.warning("Plan creation received empty required values")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Company name, plan name, and plan code are required.",
                )

            existing_plan = await self.plan_crud.get_by_plan_code(normalized_plan_code)
            if existing_plan is not None:
                logging.warning(
                    "Plan code %s already exists",
                    normalized_plan_code,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A plan with this plan code already exists.",
                )

            available_add_ons = [
                EmbeddedAddOn(
                    name=item.name,
                    description=item.description,
                    price=item.price,
                )
                for item in payload.available_add_ons
            ]
            plan = await self.plan_crud.create(
                InsuranceModel.model_validate(
                    {
                        "company_name": normalized_company_name,
                        "logo_url": payload.logo_url,
                        "plan_name": normalized_plan_name,
                        "plan_code": normalized_plan_code,
                        "insurance_type": InsuranceType(payload.insurance_type),
                        "coverage_amount": payload.coverage_amount,
                        "base_premium": payload.base_premium,
                        "duration_years": payload.duration_years,
                        "benefits": payload.benefits,
                        "terms": payload.terms,
                        "available_add_ons": available_add_ons,
                    }
                )
            )
            logging.info("Plan created successfully with code %s", normalized_plan_code)
            return self._build_plan_response(plan)
        except HTTPException as httperror:
            logging.error(
                "Error in PlanController.create_plan function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in PlanController.create_plan function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create provider insurance plan.",
            )

    async def update_plan(self, plan_code: str, payload: PlanUpdateRequest) -> PlanResponse:
        """Apply partial updates to one provider plan.

        Args:
            plan_code: Unique provider plan code to update.
            payload: Partial provider-plan updates.

        Returns:
            PlanResponse: Updated provider insurance-plan response.

        Raises:
            HTTPException: If the plan code is invalid or the plan cannot be
                updated.
        """
        try:
            logging.info("Executing PlanController.update_plan function")
            normalized_plan_code = plan_code.strip()
            if not normalized_plan_code:
                logging.warning("Empty plan_code provided for plan update")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Plan code is required.",
                )

            plan = await self.plan_crud.get_by_plan_code(normalized_plan_code)
            if plan is None:
                logging.warning("Plan not found for code %s", normalized_plan_code)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plan not found.",
                )

            updates = payload.model_dump(exclude_unset=True)
            if "company_name" in updates and updates["company_name"] is not None:
                updates["company_name"] = updates["company_name"].strip()
            if "plan_name" in updates and updates["plan_name"] is not None:
                updates["plan_name"] = updates["plan_name"].strip()
            if "plan_code" in updates and updates["plan_code"] is not None:
                updates["plan_code"] = updates["plan_code"].strip()
            if "insurance_type" in updates and updates["insurance_type"] is not None:
                updates["insurance_type"] = InsuranceType(updates["insurance_type"])
            if (
                "available_add_ons" in updates
                and updates["available_add_ons"] is not None
            ):
                updates["available_add_ons"] = [
                    EmbeddedAddOn(
                        name=PlanAddOnRequest(**item).name,
                        description=PlanAddOnRequest(**item).description,
                        price=PlanAddOnRequest(**item).price,
                    )
                    if isinstance(item, dict)
                    else EmbeddedAddOn(
                        name=item.name,
                        description=item.description,
                        price=item.price,
                    )
                    for item in updates["available_add_ons"]
                ]

            updated_plan = await self.plan_crud.update(plan, updates)
            logging.info("Plan updated successfully for code %s", normalized_plan_code)
            return self._build_plan_response(updated_plan)
        except HTTPException as httperror:
            logging.error(
                "Error in PlanController.update_plan function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in PlanController.update_plan function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update provider insurance plan.",
            )

    async def get_plan(self, plan_code: str) -> PlanResponse:
        """Return one provider plan by plan code.

        Args:
            plan_code: Unique provider plan code to fetch.

        Returns:
            PlanResponse: Serialized provider plan response.

        Raises:
            HTTPException: If the plan code is invalid or the plan cannot be
                found.
        """
        try:
            logging.info("Executing PlanController.get_plan function")
            normalized_plan_code = plan_code.strip()
            if not normalized_plan_code:
                logging.warning("Empty plan_code provided for plan lookup")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Plan code is required.",
                )

            plan = await self.plan_crud.get_by_plan_code(normalized_plan_code)
            if plan is None:
                logging.warning("Plan not found for code %s", normalized_plan_code)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plan not found.",
                )
            return self._build_plan_response(plan)
        except HTTPException as httperror:
            logging.error(
                "Error in PlanController.get_plan function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in PlanController.get_plan function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch provider insurance plan.",
            )

    async def list_plans(self) -> PlanListResponse:
        """Return all provider plans.

        Returns:
            PlanListResponse: Ordered list of provider insurance plans.

        Raises:
            HTTPException: If plan listing fails.
        """
        try:
            logging.info("Executing PlanController.list_plans function")
            plans = await self.plan_crud.list_all()
            return PlanListResponse(
                items=[self._build_plan_response(item) for item in plans],
                total_count=len(plans),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in PlanController.list_plans function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in PlanController.list_plans function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list provider insurance plans.",
            )

    def _build_plan_response(self, plan: InsuranceModel) -> PlanResponse:
        """Convert a provider plan document into the public response schema."""

        return PlanResponse(
            company_name=plan.company_name,
            logo_url=plan.logo_url,
            plan_name=plan.plan_name,
            plan_code=plan.plan_code,
            insurance_type=plan.insurance_type.value,
            coverage_amount=plan.coverage_amount,
            base_premium=plan.base_premium,
            duration_years=plan.duration_years,
            benefits=plan.benefits,
            terms=plan.terms,
            available_add_ons=[
                PlanAddOnResponse(
                    name=item.name,
                    description=item.description,
                    price=item.price,
                )
                for item in plan.available_add_ons
            ],
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

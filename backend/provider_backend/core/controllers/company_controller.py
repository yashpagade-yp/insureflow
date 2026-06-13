"""Controller logic for provider company registration and management."""

from __future__ import annotations

import secrets
from hashlib import sha256

from fastapi import HTTPException, status

from ...commons.logger import logger
from ..apis.schemas.request_schema.company_request_schema import (
    CompanyCreateRequest,
    CompanyUpdateRequest,
)
from ..apis.schemas.response_schema.company_response_schema import (
    CompanyCreateResponse,
    CompanyListResponse,
    CompanyResponse,
)
from ..cruds.company_crud import CompanyCrud
from ..models.company_model import CompanyModel, CompanyType

logging = logger(__name__)


class CompanyController:
    """Handles provider company registration and company-management logic."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependency."""

        self.company_crud = CompanyCrud()

    async def create_company(self, payload: CompanyCreateRequest) -> CompanyCreateResponse:
        """Create one provider or mediator company and return its one-time API key."""
        try:
            logging.info("Executing CompanyController.create_company function")
            existing_company = await self.company_crud.get_by_company_name(
                payload.company_name
            )
            if existing_company is not None:
                logging.warning(
                    "Company name %s already exists",
                    payload.company_name,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A company with this name already exists.",
                )

            plain_api_key = self._generate_api_key()
            company = await self.company_crud.create(
                CompanyModel(
                    company_name=payload.company_name,
                    company_type=CompanyType(payload.company_type),
                    created_by_admin_id=payload.created_by_admin_id,
                    contact_person_name=payload.contact_person_name,
                    contact_email=payload.contact_email,
                    contact_phone=payload.contact_phone,
                    api_key_hash=self._hash_api_key(plain_api_key),
                )
            )
            logging.info(
                "Company %s created successfully with code %s",
                company.company_name,
                company.company_code,
            )
            return CompanyCreateResponse(
                message="Company created successfully.",
                company=self._build_company_response(company),
                plain_api_key=plain_api_key,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in CompanyController.create_company function: %s", httperror
            )
            raise httperror
        except ValueError as error:
            logging.warning("Invalid company type provided: %s", error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid company type.",
            )
        except Exception as error:
            logging.error("Error in CompanyController.create_company function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create company.",
            )

    async def list_companies(self) -> CompanyListResponse:
        """Return all registered provider and mediator companies."""
        try:
            logging.info("Executing CompanyController.list_companies function")
            companies = await self.company_crud.list_all()
            return CompanyListResponse(
                items=[self._build_company_response(item) for item in companies],
                total_count=len(companies),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in CompanyController.list_companies function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in CompanyController.list_companies function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list companies.",
            )

    async def get_company(self, company_id: str) -> CompanyResponse:
        """Return one registered company by object id."""
        try:
            logging.info("Executing CompanyController.get_company function")
            company = await self.company_crud.get_by_id(company_id)
            if company is None:
                logging.warning("Company not found for id %s", company_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found.",
                )
            return self._build_company_response(company)
        except HTTPException as httperror:
            logging.error(
                "Error in CompanyController.get_company function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in CompanyController.get_company function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch company.",
            )

    async def update_company(
        self,
        company_id: str,
        payload: CompanyUpdateRequest,
    ) -> CompanyResponse:
        """Apply partial updates to one registered company."""
        try:
            logging.info("Executing CompanyController.update_company function")
            company = await self.company_crud.get_by_id(company_id)
            if company is None:
                logging.warning("Company not found for id %s during update", company_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found.",
                )

            updated_company = await self.company_crud.update(
                company,
                payload.model_dump(exclude_unset=True),
            )
            logging.info("Company updated successfully for id %s", company_id)
            return self._build_company_response(updated_company)
        except HTTPException as httperror:
            logging.error(
                "Error in CompanyController.update_company function: %s", httperror
            )
            raise httperror
        except Exception as error:
            logging.error("Error in CompanyController.update_company function: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update company.",
            )

    def _build_company_response(self, company: CompanyModel) -> CompanyResponse:
        """Convert a company document into the public company response schema."""

        return CompanyResponse(
            company_name=company.company_name,
            company_type=company.company_type.value,
            contact_email=company.contact_email,
            contact_phone=company.contact_phone,
            is_active=company.is_active,
            created_at=company.created_at,
            updated_at=company.updated_at,
        )

    def _generate_api_key(self) -> str:
        """Generate a one-time plain API key for a company."""

        return f"iflow_{secrets.token_urlsafe(24)}"

    def _hash_api_key(self, plain_api_key: str) -> str:
        """Hash an API key before persisting it."""

        return sha256(plain_api_key.encode("utf-8")).hexdigest()

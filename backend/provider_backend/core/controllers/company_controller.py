"""Controller logic for provider-side buyer-company and provider-company flows."""

from __future__ import annotations

import secrets
from hashlib import sha256

from fastapi import HTTPException, status

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
from core.cruds.company_crud import CompanyCrud
from core.models.company_model import CompanyModel, CompanyType

logging = logger(__name__)

BUYER_COMPANY_TYPES = [CompanyType.BUYER, CompanyType.MEDIATOR]


class CompanyController:
    """Handles buyer-company and provider-company management logic."""

    def __init__(self) -> None:
        """Initialise the controller with its CRUD dependency."""

        self.company_crud = CompanyCrud()

    async def create_buyer_company(
        self,
        payload: BuyerCompanyCreateRequest,
    ) -> CompanyCreateResponse:
        """Create one buyer company and return its one-time API key."""

        try:
            logging.info("Executing CompanyController.create_buyer_company function")
            company = await self._create_company_document(
                company_name=payload.company_name,
                company_type=CompanyType.BUYER,
                created_by_admin_id=payload.created_by_admin_id,
                contact_person_name=payload.contact_person_name,
                contact_email=payload.contact_email,
                contact_phone=payload.contact_phone,
                generate_api_key=False,
            )
            plain_api_key = self._generate_api_key()
            company.api_key_hash = self._hash_api_key(plain_api_key)
            company = await self.company_crud.update(
                company,
                {"api_key_hash": company.api_key_hash},
            )
            return CompanyCreateResponse(
                message="Buyer company created successfully.",
                company=self._build_company_response(company),
                plain_api_key=plain_api_key,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in CompanyController.create_buyer_company function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in CompanyController.create_buyer_company function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create buyer company.",
            )

    async def create_provider_company(
        self,
        payload: ProviderCompanyCreateRequest,
    ) -> CompanyCreateResponse:
        """Create one provider insurance company."""

        try:
            logging.info("Executing CompanyController.create_provider_company function")
            company = await self._create_company_document(
                company_name=payload.company_name,
                company_type=CompanyType.PROVIDER,
                created_by_admin_id=payload.created_by_admin_id,
                contact_person_name=payload.contact_person_name,
                contact_email=payload.contact_email,
                contact_phone=payload.contact_phone,
                generate_api_key=False,
            )
            return CompanyCreateResponse(
                message="Provider company created successfully.",
                company=self._build_company_response(company),
                plain_api_key=None,
            )
        except HTTPException as httperror:
            logging.error(
                "Error in CompanyController.create_provider_company function: %s",
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error(
                "Error in CompanyController.create_provider_company function: %s",
                error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create provider company.",
            )

    async def list_buyer_companies(self) -> CompanyListResponse:
        """Return all registered buyer companies."""

        return await self._list_companies_by_types(
            company_types=BUYER_COMPANY_TYPES,
            detail="Failed to list buyer companies.",
            log_name="list_buyer_companies",
        )

    async def list_provider_companies(self) -> CompanyListResponse:
        """Return all registered provider companies."""

        return await self._list_companies_by_types(
            company_types=[CompanyType.PROVIDER],
            detail="Failed to list provider companies.",
            log_name="list_provider_companies",
        )

    async def get_buyer_company(self, company_id: str) -> CompanyResponse:
        """Return one buyer company by object id."""

        return await self._get_company_by_type(
            company_id=company_id,
            allowed_types=BUYER_COMPANY_TYPES,
            not_found_detail="Buyer company not found.",
            wrong_type_detail="Requested company is not a buyer company.",
            log_name="get_buyer_company",
        )

    async def get_provider_company(self, company_id: str) -> CompanyResponse:
        """Return one provider company by object id."""

        return await self._get_company_by_type(
            company_id=company_id,
            allowed_types=[CompanyType.PROVIDER],
            not_found_detail="Provider company not found.",
            wrong_type_detail="Requested company is not a provider company.",
            log_name="get_provider_company",
        )

    async def update_buyer_company(
        self,
        company_id: str,
        payload: CompanyUpdateRequest,
    ) -> CompanyResponse:
        """Apply partial updates to one buyer company."""

        return await self._update_company_by_type(
            company_id=company_id,
            payload=payload,
            allowed_types=BUYER_COMPANY_TYPES,
            not_found_detail="Buyer company not found.",
            wrong_type_detail="Requested company is not a buyer company.",
            log_name="update_buyer_company",
        )

    async def update_provider_company(
        self,
        company_id: str,
        payload: CompanyUpdateRequest,
    ) -> CompanyResponse:
        """Apply partial updates to one provider company."""

        return await self._update_company_by_type(
            company_id=company_id,
            payload=payload,
            allowed_types=[CompanyType.PROVIDER],
            not_found_detail="Provider company not found.",
            wrong_type_detail="Requested company is not a provider company.",
            log_name="update_provider_company",
        )

    async def activate_provider_company(self, company_id: str) -> CompanyStatusResponse:
        """Activate one provider company."""

        return await self._set_provider_company_status(
            company_id=company_id,
            is_active=True,
            message="Provider company activated successfully.",
            log_name="activate_provider_company",
        )

    async def deactivate_provider_company(self, company_id: str) -> CompanyStatusResponse:
        """Deactivate one provider company."""

        return await self._set_provider_company_status(
            company_id=company_id,
            is_active=False,
            message="Provider company deactivated successfully.",
            log_name="deactivate_provider_company",
        )

    async def _create_company_document(
        self,
        *,
        company_name: str,
        company_type: CompanyType,
        created_by_admin_id: str,
        contact_person_name: str | None,
        contact_email: str | None,
        contact_phone: str | None,
        generate_api_key: bool,
    ) -> CompanyModel:
        """Create and persist one company document after validation."""

        normalized_company_name = company_name.strip()
        if not normalized_company_name:
            logging.warning("Empty company name provided for company creation")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name is required.",
            )

        existing_company = await self.company_crud.get_by_company_name(
            normalized_company_name
        )
        if existing_company is not None:
            logging.warning("Company name %s already exists", normalized_company_name)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A company with this name already exists.",
            )

        api_key_hash = None
        if generate_api_key:
            api_key_hash = self._hash_api_key(self._generate_api_key())

        company = await self.company_crud.create(
            CompanyModel.model_validate(
                {
                    "company_name": normalized_company_name,
                    "company_type": company_type,
                    "created_by_admin_id": created_by_admin_id,
                    "contact_person_name": (
                        contact_person_name.strip()
                        if contact_person_name is not None and contact_person_name.strip()
                        else None
                    ),
                    "contact_email": (
                        contact_email.strip().lower()
                        if contact_email is not None and contact_email.strip()
                        else None
                    ),
                    "contact_phone": (
                        contact_phone.strip()
                        if contact_phone is not None and contact_phone.strip()
                        else None
                    ),
                    "api_key_hash": api_key_hash or "",
                }
            )
        )
        logging.info(
            "Company %s created successfully with code %s and type %s",
            company.company_name,
            company.company_code,
            company.company_type.value,
        )
        return company

    async def _list_companies_by_types(
        self,
        *,
        company_types: list[CompanyType],
        detail: str,
        log_name: str,
    ) -> CompanyListResponse:
        """Return all companies matching the requested company types."""

        try:
            logging.info("Executing CompanyController.%s function", log_name)
            companies = await self.company_crud.list_by_company_types(company_types)
            return CompanyListResponse(
                items=[self._build_company_response(item) for item in companies],
                total_count=len(companies),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in CompanyController.%s function: %s",
                log_name,
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error("Error in CompanyController.%s function: %s", log_name, error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail,
            )

    async def _get_company_by_type(
        self,
        *,
        company_id: str,
        allowed_types: list[CompanyType],
        not_found_detail: str,
        wrong_type_detail: str,
        log_name: str,
    ) -> CompanyResponse:
        """Return one company by id after validating its company type."""

        try:
            logging.info("Executing CompanyController.%s function", log_name)
            company = await self._get_validated_company(
                company_id=company_id,
                allowed_types=allowed_types,
                not_found_detail=not_found_detail,
                wrong_type_detail=wrong_type_detail,
            )
            return self._build_company_response(company)
        except HTTPException as httperror:
            logging.error(
                "Error in CompanyController.%s function: %s",
                log_name,
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error("Error in CompanyController.%s function: %s", log_name, error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch company.",
            )

    async def _update_company_by_type(
        self,
        *,
        company_id: str,
        payload: CompanyUpdateRequest,
        allowed_types: list[CompanyType],
        not_found_detail: str,
        wrong_type_detail: str,
        log_name: str,
    ) -> CompanyResponse:
        """Apply partial updates to one company after validating its type."""

        try:
            logging.info("Executing CompanyController.%s function", log_name)
            company = await self._get_validated_company(
                company_id=company_id,
                allowed_types=allowed_types,
                not_found_detail=not_found_detail,
                wrong_type_detail=wrong_type_detail,
            )
            updates = payload.model_dump(exclude_unset=True)
            if "contact_person_name" in updates and updates["contact_person_name"] is not None:
                updates["contact_person_name"] = updates["contact_person_name"].strip() or None
            if "contact_email" in updates and updates["contact_email"] is not None:
                updates["contact_email"] = updates["contact_email"].strip().lower() or None
            if "contact_phone" in updates and updates["contact_phone"] is not None:
                updates["contact_phone"] = updates["contact_phone"].strip() or None

            updated_company = await self.company_crud.update(company, updates)
            return self._build_company_response(updated_company)
        except HTTPException as httperror:
            logging.error(
                "Error in CompanyController.%s function: %s",
                log_name,
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error("Error in CompanyController.%s function: %s", log_name, error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update company.",
            )

    async def _set_provider_company_status(
        self,
        *,
        company_id: str,
        is_active: bool,
        message: str,
        log_name: str,
    ) -> CompanyStatusResponse:
        """Activate or deactivate one provider company."""

        try:
            logging.info("Executing CompanyController.%s function", log_name)
            company = await self._get_validated_company(
                company_id=company_id,
                allowed_types=[CompanyType.PROVIDER],
                not_found_detail="Provider company not found.",
                wrong_type_detail="Requested company is not a provider company.",
            )
            updated_company = await self.company_crud.update(
                company,
                {"is_active": is_active},
            )
            return CompanyStatusResponse(
                message=message,
                company=self._build_company_response(updated_company),
            )
        except HTTPException as httperror:
            logging.error(
                "Error in CompanyController.%s function: %s",
                log_name,
                httperror,
            )
            raise httperror
        except Exception as error:
            logging.error("Error in CompanyController.%s function: %s", log_name, error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update provider-company status.",
            )

    async def _get_validated_company(
        self,
        *,
        company_id: str,
        allowed_types: list[CompanyType],
        not_found_detail: str,
        wrong_type_detail: str,
    ) -> CompanyModel:
        """Fetch one company by id and validate its company type."""

        normalized_company_id = company_id.strip()
        if not normalized_company_id:
            logging.warning("Empty company_id provided for company lookup")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company id is required.",
            )

        company = await self.company_crud.get_by_id(normalized_company_id)
        if company is None:
            logging.warning("Company not found for id %s", normalized_company_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=not_found_detail,
            )

        if company.company_type not in allowed_types:
            logging.warning(
                "Company %s with type %s failed company-type validation",
                normalized_company_id,
                company.company_type.value,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=wrong_type_detail,
            )

        return company

    def _build_company_response(self, company: CompanyModel) -> CompanyResponse:
        """Convert a company document into the public company response schema."""

        company_type = company.company_type.value
        if company.company_type == CompanyType.MEDIATOR:
            company_type = CompanyType.BUYER.value

        return CompanyResponse(
            id=str(company.id),
            company_code=company.company_code,
            company_name=company.company_name,
            company_type=company_type,
            contact_person_name=company.contact_person_name,
            contact_email=company.contact_email,
            contact_phone=company.contact_phone,
            is_active=company.is_active,
            created_at=company.created_at,
            updated_at=company.updated_at,
        )

    def _generate_api_key(self) -> str:
        """Generate a one-time plain API key for a buyer company."""

        return f"iflow_{secrets.token_urlsafe(24)}"

    def _hash_api_key(self, plain_api_key: str) -> str:
        """Hash an API key before persisting it."""

        return sha256(plain_api_key.encode("utf-8")).hexdigest()

"""Buyer-company API-key validation helpers for provider-backend integrations."""

from __future__ import annotations

from hashlib import sha256
from typing import Annotated

from fastapi import Header, HTTPException, status

from commons.logger import logger
from core.cruds.company_crud import CompanyCrud
from core.models.company_model import CompanyModel, CompanyType

logging = logger(__name__)


class BrokerAuthService:
    """Validates buyer-company API keys for inter-backend requests."""

    def __init__(self) -> None:
        """Initialise the service with its CRUD dependency."""

        self.company_crud = CompanyCrud()

    async def validate_api_key(self, api_key: str) -> CompanyModel:
        """Validate an incoming plain API key against registered buyer companies."""

        normalized_api_key = api_key.strip()
        if normalized_api_key.startswith("Bearer "):
            normalized_api_key = normalized_api_key[7:].strip()

        if not normalized_api_key:
            logging.warning("Empty API key provided for provider-backend integration")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing provider integration API key.",
            )

        hashed_api_key = sha256(normalized_api_key.encode("utf-8")).hexdigest()
        company = await self.company_crud.get_by_api_key_hash(hashed_api_key)
        if company is None:
            logging.warning("Invalid API key provided for provider-backend integration")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid provider integration API key.",
            )

        if company.company_type not in [CompanyType.BUYER, CompanyType.MEDIATOR]:
            logging.warning(
                "Company %s attempted integration access with non-buyer API key",
                company.company_name,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This API key is not permitted for buyer-company integration access.",
            )

        if not company.is_active:
            logging.warning(
                "Inactive buyer company %s attempted integration access",
                company.company_name,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This buyer-company integration is inactive.",
            )

        logging.info(
            "Buyer-company API key validated successfully for company %s",
            company.company_name,
        )
        return company


async def validate_broker_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> CompanyModel:
    """FastAPI dependency that validates broker API key headers for integration routes."""

    if x_api_key is None:
        logging.warning("Missing X-API-Key header for provider-backend integration route")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing provider integration API key.",
        )

    return await BrokerAuthService().validate_api_key(x_api_key)

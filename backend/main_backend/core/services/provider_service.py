"""Service client for main-backend communication with the provider backend."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, status

from commons.logger import logger

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

logging = logger(__name__)


def _get_provider_backend_url() -> str:
    """Read the provider backend base URL from the environment."""

    return os.getenv("PROVIDER_BACKEND_URL", "http://localhost:5200").strip()


def _get_provider_api_key() -> str:
    """Read and normalize the inter-service API key from the environment."""

    raw_api_key = os.getenv("INSUREFLOW_API_KEY", "").strip()
    if raw_api_key.startswith("Bearer "):
        return raw_api_key[7:].strip()
    return raw_api_key


def _get_auth_headers() -> dict[str, str]:
    """Build authentication headers for provider-backend requests."""

    api_key = _get_provider_api_key()
    if not api_key:
        logging.error(
            "INSUREFLOW_API_KEY is not set in main_backend/.env for provider communication"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider service is not configured. Please contact the administrator.",
        )
    return {"X-API-Key": api_key}


def _handle_provider_response(response: httpx.Response, context: str) -> dict[str, Any]:
    """Inspect provider-backend responses and convert failures into clean HTTP errors."""

    logging.info(
        "Provider backend responded [%s] for %s",
        response.status_code,
        context,
    )

    if response.status_code in (200, 201):
        return response.json()

    try:
        response_body = response.json()
    except Exception:
        response_body = {}

    detail = response_body.get("detail", "Provider backend request failed.")

    if response.status_code == 400:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if response.status_code == 401:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
    if response.status_code == 403:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
    if response.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    if response.status_code == 409:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    if response.status_code == 429:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )

    logging.error(
        "Provider backend returned unexpected status %s for %s",
        response.status_code,
        context,
    )
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Provider backend returned an unexpected error. Please try again later.",
    )


class ProviderService:
    """Encapsulates HTTP communication from main backend to provider backend."""

    async def generate_quotes(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call the provider backend to generate quotes for a transaction."""

        context = f"generate_quotes for transaction {payload.get('transaction_id')}"
        provider_backend_url = _get_provider_backend_url()
        logging.info(
            "Calling provider backend: %s | base_url=%s",
            context,
            provider_backend_url,
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{provider_backend_url}/v1/quotes/generate",
                    json=payload,
                    headers=_get_auth_headers(),
                    timeout=15.0,
                )
            return _handle_provider_response(response, context)
        except HTTPException:
            raise
        except httpx.ConnectError:
            logging.error("Cannot reach provider backend for %s", context)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Provider service is currently unreachable. Please try again later.",
            )
        except Exception as error:
            logging.error("Unexpected error in ProviderService.generate_quotes: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with provider quote service.",
            )

    async def get_quotes(self, transaction_id: str) -> dict[str, Any]:
        """Call the provider backend to fetch generated quotes for a transaction."""

        context = f"get_quotes for transaction {transaction_id}"
        provider_backend_url = _get_provider_backend_url()
        logging.info(
            "Calling provider backend: %s | base_url=%s",
            context,
            provider_backend_url,
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{provider_backend_url}/v1/quotes/{transaction_id}",
                    headers=_get_auth_headers(),
                    timeout=10.0,
                )
            return _handle_provider_response(response, context)
        except HTTPException:
            raise
        except httpx.ConnectError:
            logging.error("Cannot reach provider backend for %s", context)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Provider service is currently unreachable. Please try again later.",
            )
        except Exception as error:
            logging.error("Unexpected error in ProviderService.get_quotes: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with provider quote service.",
            )

    async def select_plan(self, transaction_id: str, selected_plan_id: str) -> dict[str, Any]:
        """Call the provider backend to mark a plan as selected."""

        context = f"select_plan {selected_plan_id} for transaction {transaction_id}"
        provider_backend_url = _get_provider_backend_url()
        logging.info(
            "Calling provider backend: %s | base_url=%s",
            context,
            provider_backend_url,
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{provider_backend_url}/v1/quotes/{transaction_id}/select-plan/{selected_plan_id}",
                    headers=_get_auth_headers(),
                    timeout=10.0,
                )
            return _handle_provider_response(response, context)
        except HTTPException:
            raise
        except httpx.ConnectError:
            logging.error("Cannot reach provider backend for %s", context)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Provider service is currently unreachable. Please try again later.",
            )
        except Exception as error:
            logging.error("Unexpected error in ProviderService.select_plan: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with provider quote service.",
            )

    async def update_add_ons(
        self,
        transaction_id: str,
        selected_plan_id: str,
        selected_add_ons: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Call the provider backend to save selected add-ons for a plan."""

        context = f"update_add_ons {selected_plan_id} for transaction {transaction_id}"
        provider_backend_url = _get_provider_backend_url()
        logging.info(
            "Calling provider backend: %s | base_url=%s",
            context,
            provider_backend_url,
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{provider_backend_url}/v1/quotes/{transaction_id}/select-add-ons/{selected_plan_id}",
                    json={"selected_add_ons": selected_add_ons},
                    headers=_get_auth_headers(),
                    timeout=10.0,
                )
            return _handle_provider_response(response, context)
        except HTTPException:
            raise
        except httpx.ConnectError:
            logging.error("Cannot reach provider backend for %s", context)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Provider service is currently unreachable. Please try again later.",
            )
        except Exception as error:
            logging.error("Unexpected error in ProviderService.update_add_ons: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with provider quote service.",
            )

    async def create_payment(
        self,
        transaction_id: str,
        user_id: str,
        amount: float,
    ) -> dict[str, Any]:
        """Call the provider backend to create a payment record."""

        context = f"create_payment for transaction {transaction_id}"
        provider_backend_url = _get_provider_backend_url()
        logging.info(
            "Calling provider backend: %s | base_url=%s",
            context,
            provider_backend_url,
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{provider_backend_url}/v1/payments",
                    json={
                        "transaction_id": transaction_id,
                        "user_id": user_id,
                        "amount": amount,
                    },
                    headers=_get_auth_headers(),
                    timeout=10.0,
                )
            return _handle_provider_response(response, context)
        except HTTPException:
            raise
        except httpx.ConnectError:
            logging.error("Cannot reach provider backend for %s", context)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Provider service is currently unreachable. Please try again later.",
            )
        except Exception as error:
            logging.error("Unexpected error in ProviderService.create_payment: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with provider payment service.",
            )

    async def send_payment_otp(self, payment_reference: str) -> dict[str, Any]:
        """Call the provider backend to generate a payment OTP."""

        context = f"send_payment_otp for payment reference {payment_reference}"
        provider_backend_url = _get_provider_backend_url()
        logging.info(
            "Calling provider backend: %s | base_url=%s",
            context,
            provider_backend_url,
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{provider_backend_url}/v1/payments/{payment_reference}/send-otp",
                    headers=_get_auth_headers(),
                    timeout=10.0,
                )
            return _handle_provider_response(response, context)
        except HTTPException:
            raise
        except httpx.ConnectError:
            logging.error("Cannot reach provider backend for %s", context)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Provider service is currently unreachable. Please try again later.",
            )
        except Exception as error:
            logging.error("Unexpected error in ProviderService.send_payment_otp: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with provider payment service.",
            )

    async def verify_payment_otp(
        self,
        transaction_id: str,
        payment_reference: str,
        otp: str,
    ) -> dict[str, Any]:
        """Call the provider backend to verify a payment OTP."""

        context = f"verify_payment_otp for transaction {transaction_id}"
        provider_backend_url = _get_provider_backend_url()
        logging.info(
            "Calling provider backend: %s | base_url=%s",
            context,
            provider_backend_url,
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{provider_backend_url}/v1/payments/verify-otp",
                    json={
                        "transaction_id": transaction_id,
                        "payment_reference": payment_reference,
                        "otp": otp,
                    },
                    headers=_get_auth_headers(),
                    timeout=10.0,
                )
            return _handle_provider_response(response, context)
        except HTTPException:
            raise
        except httpx.ConnectError:
            logging.error("Cannot reach provider backend for %s", context)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Provider service is currently unreachable. Please try again later.",
            )
        except Exception as error:
            logging.error("Unexpected error in ProviderService.verify_payment_otp: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with provider payment service.",
            )

    async def get_payment_status(self, payment_reference: str) -> dict[str, Any]:
        """Call the provider backend to fetch payment status details."""

        context = f"get_payment_status for payment reference {payment_reference}"
        provider_backend_url = _get_provider_backend_url()
        logging.info(
            "Calling provider backend: %s | base_url=%s",
            context,
            provider_backend_url,
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{provider_backend_url}/v1/payments/{payment_reference}/status",
                    headers=_get_auth_headers(),
                    timeout=10.0,
                )
            return _handle_provider_response(response, context)
        except HTTPException:
            raise
        except httpx.ConnectError:
            logging.error("Cannot reach provider backend for %s", context)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Provider service is currently unreachable. Please try again later.",
            )
        except Exception as error:
            logging.error("Unexpected error in ProviderService.get_payment_status: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with provider payment service.",
            )

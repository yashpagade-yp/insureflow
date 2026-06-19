"""Calling-bot routes for the InsureFlow main backend."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decodeJWT
from commons.logger import logger
from core.apis.schemas.request_schema.calling_bot_request_schema import (
    CallingBotCompletePurchaseRequest,
    CallingBotPreparePurchaseRequest,
    CallingBotStartCallRequest,
)
from core.apis.schemas.response_schema.calling_bot_response_schema import (
    CallingBotCallDetailResponse,
    CallingBotCallListResponse,
    CallingBotCompletePurchaseResponse,
    CallingBotConfigResponse,
    CallingBotPreparePurchaseResponse,
    CallingBotStartCallResponse,
)
from core.controllers.calling_bot_controller import CallingBotController

logging = logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/login-otp/verify")
calling_bot_router = APIRouter(tags=["calling-bot"])
calling_bot_controller = CallingBotController()


def _get_authenticated_admin(token: str) -> dict:
    """Validate a JWT token and ensure the caller is a customer-app admin."""

    authenticated_user_details = decodeJWT(token=token)
    if not authenticated_user_details:
        logging.warning("Invalid or expired token provided for calling-bot routes")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if authenticated_user_details.get("user_role") != "ADMIN":
        logging.warning(
            "Unauthorized access attempt to calling-bot route by user ID %s",
            authenticated_user_details.get("id"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
    return authenticated_user_details


@calling_bot_router.get(
    "/v1/admins/calling-bot/config",
    response_model=CallingBotConfigResponse,
    status_code=status.HTTP_200_OK,
)
async def get_calling_bot_config(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CallingBotConfigResponse:
    """Return safe calling-bot configuration for the customer-app admin frontend."""

    try:
        logging.info("Calling GET /v1/admins/calling-bot/config endpoint")
        _get_authenticated_admin(token)
        return await calling_bot_controller.get_safe_config()
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/admins/calling-bot/config endpoint: %s",
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/admins/calling-bot/config endpoint: %s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch calling-bot configuration.",
        )


@calling_bot_router.post(
    "/v1/admins/calling-bot/calls",
    response_model=CallingBotStartCallResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_calling_bot_call(
    payload: CallingBotStartCallRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CallingBotStartCallResponse:
    """Start one outbound Twilio calling-bot call from the customer-app admin side."""

    try:
        logging.info("Calling POST /v1/admins/calling-bot/calls endpoint")
        admin_user = _get_authenticated_admin(token)
        return await calling_bot_controller.start_outbound_call(
            payload=payload,
            admin_id=admin_user.get("id", ""),
            admin_email=admin_user.get("email", ""),
        )
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/admins/calling-bot/calls endpoint: %s",
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/admins/calling-bot/calls endpoint: %s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start the calling-bot outbound call.",
        )


@calling_bot_router.get(
    "/v1/admins/calling-bot/calls",
    response_model=CallingBotCallListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_calling_bot_calls(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CallingBotCallListResponse:
    """Return all customer-app calling-bot calls for admin monitoring."""

    try:
        logging.info("Calling GET /v1/admins/calling-bot/calls endpoint")
        _get_authenticated_admin(token)
        return await calling_bot_controller.list_calls()
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/admins/calling-bot/calls endpoint: %s",
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/admins/calling-bot/calls endpoint: %s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list calling-bot calls.",
        )


@calling_bot_router.get(
    "/v1/admins/calling-bot/calls/{call_reference}",
    response_model=CallingBotCallDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_calling_bot_call(
    call_reference: str,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CallingBotCallDetailResponse:
    """Return one detailed calling-bot call record for the admin frontend."""

    try:
        logging.info(
            "Calling GET /v1/admins/calling-bot/calls/%s endpoint",
            call_reference,
        )
        _get_authenticated_admin(token)
        return await calling_bot_controller.get_call_detail(call_reference)
    except HTTPException as httperror:
        logging.error(
            "Error in GET /v1/admins/calling-bot/calls/%s endpoint: %s",
            call_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in GET /v1/admins/calling-bot/calls/%s endpoint: %s",
            call_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch calling-bot call details.",
        )


@calling_bot_router.post(
    "/v1/admins/calling-bot/calls/{call_reference}/prepare-purchase",
    response_model=CallingBotPreparePurchaseResponse,
    status_code=status.HTTP_200_OK,
)
async def prepare_calling_bot_purchase(
    call_reference: str,
    payload: CallingBotPreparePurchaseRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CallingBotPreparePurchaseResponse:
    """Prepare the selected plan payment flow and generate the mock OTP."""

    try:
        logging.info(
            "Calling POST /v1/admins/calling-bot/calls/%s/prepare-purchase endpoint",
            call_reference,
        )
        _get_authenticated_admin(token)
        return await calling_bot_controller.prepare_purchase(call_reference, payload)
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/admins/calling-bot/calls/%s/prepare-purchase endpoint: %s",
            call_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/admins/calling-bot/calls/%s/prepare-purchase endpoint: %s",
            call_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prepare the calling-bot purchase flow.",
        )


@calling_bot_router.post(
    "/v1/admins/calling-bot/calls/{call_reference}/complete-purchase",
    response_model=CallingBotCompletePurchaseResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_calling_bot_purchase(
    call_reference: str,
    payload: CallingBotCompletePurchaseRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CallingBotCompletePurchaseResponse:
    """Complete the mock purchase flow for a calling-bot call."""

    try:
        logging.info(
            "Calling POST /v1/admins/calling-bot/calls/%s/complete-purchase endpoint",
            call_reference,
        )
        _get_authenticated_admin(token)
        return await calling_bot_controller.complete_purchase(call_reference, payload)
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/admins/calling-bot/calls/%s/complete-purchase endpoint: %s",
            call_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/admins/calling-bot/calls/%s/complete-purchase endpoint: %s",
            call_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete the calling-bot purchase flow.",
        )


@calling_bot_router.post(
    "/v1/calling-bot/twiml/outbound/{call_reference}",
    status_code=status.HTTP_200_OK,
)
async def get_calling_bot_twiml(
    call_reference: str,
) -> Response:
    """Return the first TwiML document for the outbound bot call."""

    try:
        logging.info(
            "Calling POST /v1/calling-bot/twiml/outbound/%s endpoint",
            call_reference,
        )
        twiml = await calling_bot_controller.build_initial_twiml(call_reference)
        return Response(content=twiml, media_type="application/xml")
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s endpoint: %s",
            call_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s endpoint: %s",
            call_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate the calling-bot voice response.",
        )


@calling_bot_router.post(
    "/v1/calling-bot/twiml/outbound/{call_reference}/interest",
    status_code=status.HTTP_200_OK,
)
async def process_interest_capture(
    call_reference: str,
    Digits: str | None = Form(default=None),
    SpeechResult: str | None = Form(default=None),
) -> Response:
    """Process customer interest capture and return the next TwiML prompt."""

    try:
        logging.info(
            "Calling POST /v1/calling-bot/twiml/outbound/%s/interest endpoint",
            call_reference,
        )
        twiml = await calling_bot_controller.process_interest_response(
            call_reference=call_reference,
            digits=Digits,
            speech_result=SpeechResult,
        )
        return Response(content=twiml, media_type="application/xml")
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/interest endpoint: %s",
            call_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/interest endpoint: %s",
            call_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the calling-bot interest capture.",
        )


@calling_bot_router.post(
    "/v1/calling-bot/twiml/outbound/{call_reference}/confirm-details",
    status_code=status.HTTP_200_OK,
)
async def process_detail_confirmation(
    call_reference: str,
    Digits: str | None = Form(default=None),
    SpeechResult: str | None = Form(default=None),
) -> Response:
    """Confirm known customer details and return the next TwiML prompt."""

    try:
        logging.info(
            "Calling POST /v1/calling-bot/twiml/outbound/%s/confirm-details endpoint",
            call_reference,
        )
        twiml = await calling_bot_controller.process_detail_confirmation_response(
            call_reference=call_reference,
            digits=Digits,
            speech_result=SpeechResult,
        )
        return Response(content=twiml, media_type="application/xml")
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/confirm-details endpoint: %s",
            call_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/confirm-details endpoint: %s",
            call_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm the calling-bot customer details.",
        )


@calling_bot_router.post(
    "/v1/calling-bot/twiml/outbound/{call_reference}/coverage",
    status_code=status.HTTP_200_OK,
)
async def process_coverage_capture(
    call_reference: str,
    Digits: str | None = Form(default=None),
    SpeechResult: str | None = Form(default=None),
) -> Response:
    """Capture coverage amount, prepare matching plans, and return TwiML summary."""

    try:
        logging.info(
            "Calling POST /v1/calling-bot/twiml/outbound/%s/coverage endpoint",
            call_reference,
        )
        twiml = await calling_bot_controller.process_coverage_response(
            call_reference=call_reference,
            digits=Digits,
            speech_result=SpeechResult,
        )
        return Response(content=twiml, media_type="application/xml")
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/coverage endpoint: %s",
            call_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/coverage endpoint: %s",
            call_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the calling-bot coverage capture.",
        )


@calling_bot_router.post(
    "/v1/calling-bot/twiml/outbound/{call_reference}/plan-choice",
    status_code=status.HTTP_200_OK,
)
async def process_plan_choice_capture(
    call_reference: str,
    Digits: str | None = Form(default=None),
    SpeechResult: str | None = Form(default=None),
) -> Response:
    """Capture the customer's selected plan and return the next TwiML prompt."""

    try:
        logging.info(
            "Calling POST /v1/calling-bot/twiml/outbound/%s/plan-choice endpoint",
            call_reference,
        )
        twiml = await calling_bot_controller.process_plan_selection_response(
            call_reference=call_reference,
            digits=Digits,
            speech_result=SpeechResult,
        )
        return Response(content=twiml, media_type="application/xml")
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/plan-choice endpoint: %s",
            call_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/plan-choice endpoint: %s",
            call_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the calling-bot plan selection.",
        )


@calling_bot_router.post(
    "/v1/calling-bot/twiml/outbound/{call_reference}/payment-confirmation",
    status_code=status.HTTP_200_OK,
)
async def process_payment_confirmation_capture(
    call_reference: str,
    Digits: str | None = Form(default=None),
    SpeechResult: str | None = Form(default=None),
) -> Response:
    """Capture whether the customer wants to continue payment verification now."""

    try:
        logging.info(
            "Calling POST /v1/calling-bot/twiml/outbound/%s/payment-confirmation endpoint",
            call_reference,
        )
        twiml = await calling_bot_controller.process_payment_confirmation_response(
            call_reference=call_reference,
            digits=Digits,
            speech_result=SpeechResult,
        )
        return Response(content=twiml, media_type="application/xml")
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/payment-confirmation endpoint: %s",
            call_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/payment-confirmation endpoint: %s",
            call_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the calling-bot payment confirmation step.",
        )


@calling_bot_router.post(
    "/v1/calling-bot/twiml/outbound/{call_reference}/payment-otp",
    status_code=status.HTTP_200_OK,
)
async def process_payment_otp_capture(
    call_reference: str,
    Digits: str | None = Form(default=None),
    SpeechResult: str | None = Form(default=None),
) -> Response:
    """Capture the payment OTP and continue the purchase flow."""

    try:
        logging.info(
            "Calling POST /v1/calling-bot/twiml/outbound/%s/payment-otp endpoint",
            call_reference,
        )
        twiml = await calling_bot_controller.process_payment_otp_response(
            call_reference=call_reference,
            digits=Digits,
            speech_result=SpeechResult,
        )
        return Response(content=twiml, media_type="application/xml")
    except HTTPException as httperror:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/payment-otp endpoint: %s",
            call_reference,
            httperror,
        )
        raise httperror
    except Exception as error:
        logging.error(
            "Error in POST /v1/calling-bot/twiml/outbound/%s/payment-otp endpoint: %s",
            call_reference,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the calling-bot payment OTP step.",
        )


@calling_bot_router.post(
    "/v1/calling-bot/calls/status/{call_reference}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def receive_call_status_callback(
    call_reference: str,
    request: Request,
) -> Response:
    """Receive Twilio call status callbacks and persist call-state changes."""

    try:
        logging.info(
            "Calling POST /v1/calling-bot/calls/status/%s endpoint",
            call_reference,
        )
        form_data = await request.form()
        callback_payload = {key: value for key, value in form_data.items()}
        await calling_bot_controller.update_call_status_from_callback(
            call_reference=call_reference,
            callback_payload=callback_payload,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as error:
        logging.error(
            "Error in POST /v1/calling-bot/calls/status/%s endpoint: %s",
            call_reference,
            error,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

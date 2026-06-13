"""Central API router registration for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter

from .routers.company_router import router as company_router
from .routers.payment_router import router as payment_router
from .routers.plan_router import router as plan_router
from .routers.provider_auth_router import router as provider_auth_router
from .routers.quote_router import router as quote_router

router = APIRouter()
router.include_router(provider_auth_router)
router.include_router(company_router)
router.include_router(plan_router)
router.include_router(quote_router)
router.include_router(payment_router)

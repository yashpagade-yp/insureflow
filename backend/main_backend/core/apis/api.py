"""API router registration for the InsureFlow main backend."""

from __future__ import annotations

from fastapi import APIRouter

from .routers.insurance_detail_router import insurance_detail_router
from .routers.policy_router import policy_router
from .routers.transaction_router import transaction_router
from .routers.user_router import user_router

router = APIRouter()

router.include_router(user_router)
router.include_router(insurance_detail_router)
router.include_router(transaction_router)
router.include_router(policy_router)

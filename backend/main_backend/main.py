"""Application entrypoint for the InsureFlow main backend."""

from __future__ import annotations

from fastapi import FastAPI

from core.apis.api import router as api_router


app = FastAPI(
    title="InsureFlow Main Backend",
    version="1.0.0",
    description="Main backend for customer journeys, transactions, and policies.",
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return a simple health-check response."""

    return {"status": "ok"}

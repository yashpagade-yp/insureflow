"""Application entrypoint for the InsureFlow main backend."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.apis.api import router as api_router
from core.database.database import close_mongo_connection, connect_to_mongo
from core.services.admin_sync_service import sync_provider_admins_to_main


app = FastAPI(
    title="InsureFlow Main Backend",
    version="1.0.0",
    description="Main backend for customer journeys, transactions, and policies.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3001",
        "http://localhost:3001",
        "http://127.0.0.1:3002",
        "http://localhost:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

generated_policies_dir = Path(__file__).resolve().parent / "generated_policies"
generated_policies_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/generated-policies",
    StaticFiles(directory=generated_policies_dir),
    name="generated-policies",
)

app.include_router(api_router)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialise database connectivity and sync shared admin accounts."""

    await connect_to_mongo()
    await sync_provider_admins_to_main()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close the shared MongoDB connection cleanly."""

    await close_mongo_connection()


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return a simple health-check response."""

    return {"status": "ok"}

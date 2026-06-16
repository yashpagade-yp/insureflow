"""Application entrypoint for the InsureFlow provider backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.apis.api import router as api_router


app = FastAPI(
    title="InsureFlow Provider Backend",
    version="1.0.0",
    description="Provider backend for admin auth, companies, plans, quotes, and payments.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3001",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return a simple health-check response for the provider backend."""

    return {"status": "ok"}

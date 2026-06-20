"""Configuration for the InsureFlow MCP server.

Holds base URLs for both backends and any shared settings.
"""

from __future__ import annotations

import os

MAIN_BACKEND_URL = os.getenv("MAIN_BACKEND_URL", "http://localhost:8000").strip()
PROVIDER_BACKEND_URL = os.getenv("PROVIDER_BACKEND_URL", "http://localhost:8001").strip()

# MCP server host and port (Streamable HTTP transport)
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0").strip()
MCP_PORT = int(os.getenv("MCP_PORT", "8080"))

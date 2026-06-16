"""Configuration for the InsureFlow MCP server.

Holds base URLs for both backends and any shared settings.
"""

from __future__ import annotations

MAIN_BACKEND_URL = "http://localhost:8000"
PROVIDER_BACKEND_URL = "http://localhost:8001"

# MCP server host and port (Streamable HTTP transport)
MCP_HOST = "0.0.0.0"
MCP_PORT = 8080

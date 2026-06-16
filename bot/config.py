"""
InsureFlow Bot — Configuration
================================
Loads all environment variables from .env and exposes them as constants.
Every other file imports from here — never read os.getenv() directly elsewhere.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass(frozen=True)
class BotConfig:
    # LLM
    groq_api_key: str
    groq_model: str

    # STT (Voice Bot only)
    deepgram_api_key: str

    # TTS (Voice Bot only)
    cartesia_api_key: str
    cartesia_voice_id: str

    # MCP Server
    mcp_server_url: str

    # Server
    host: str
    port: int


def load_config() -> BotConfig:
    """Load and validate all required environment variables."""

    required = {
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
        "DEEPGRAM_API_KEY": os.getenv("DEEPGRAM_API_KEY", ""),
        "CARTESIA_API_KEY": os.getenv("CARTESIA_API_KEY", ""),
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Check your bot/.env file."
        )

    return BotConfig(
        # LLM — Groq with Llama 3.3 (fast + supports function calling)
        groq_api_key=required["GROQ_API_KEY"],
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),

        # STT
        deepgram_api_key=required["DEEPGRAM_API_KEY"],

        # TTS — Cartesia "Sonic" voice (clear, professional)
        cartesia_api_key=required["CARTESIA_API_KEY"],
        cartesia_voice_id=os.getenv("CARTESIA_VOICE_ID", "79a125e8-cd45-4c13-8a67-188112f4dd22"),

        # MCP Server
        mcp_server_url=os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp"),

        # Server
        host=os.getenv("BOT_HOST", "0.0.0.0"),
        port=int(os.getenv("BOT_PORT", "8002")),
    )


# Single global config instance — import this everywhere
config = load_config()

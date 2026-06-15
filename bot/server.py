"""
InsureFlow Bot — FastAPI Server
================================
HTTP server that hosts both the chatbot and voice bot endpoints.

Endpoints:
    GET  /            → health check
    POST /api/chat    → chatbot REST API (JSON request/response)
    POST /voice/offer → voice bot (WebRTC SDP offer/answer handshake)
    POST /voice/ice   → voice bot (ICE candidate exchange)

Ports:
    main_backend     : 8000
    provider_backend : 8001
    bot server       : 8002  ← this
    mcp server       : 8080
    frontend         : 5173
"""

import asyncio
import json
import uuid

import httpx
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from groq import AsyncGroq
from loguru import logger
from pydantic import BaseModel

# SmallWebRTC connection handling
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection

from config import config
from system_prompt import SYSTEM_PROMPT
from mcp_client import TOOLS
from chatbot import run_chatbot
from voicebot import run_voicebot


# ── App Setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="InsureFlow Bot Server",
    description="Voice Bot and Chat Bot for InsureFlow customer journey",
    version="1.0.0",
)

# CORS — allow the frontend to connect from any localhost port
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Models ────────────────────────────────────────────────────────────

class RTCOffer(BaseModel):
    """WebRTC SDP offer from browser."""
    sdp: str
    type: str


class ICECandidate(BaseModel):
    """WebRTC ICE candidate for network traversal."""
    candidate: str
    sdpMid: str | None = None
    sdpMLineIndex: int | None = None


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""
    session_id: str | None = None   # None = start new session
    message: str


# ── In-Memory Chat Sessions ───────────────────────────────────────────────────
# Each session holds the full conversation history for one browser tab.
# Format: {session_id: [{"role": ..., "content": ...}, ...]}
_chat_sessions: dict[str, list] = {}


# ── Active Sessions ───────────────────────────────────────────────────────────
# Track active SmallWebRTC connections by session ID
# Used to route ICE candidates to the right session
_voice_connections: dict[str, SmallWebRTCConnection] = {}


# ── Health Check ──────────────────────────────────────────────────────────────

@app.get("/")
async def health_check():
    """Health check — confirms bot server is running."""
    return {
        "status": "ok",
        "service": "InsureFlow Bot Server",
        "endpoints": {
            "chat": "POST http://localhost:8002/api/chat",
            "voicebot_offer": "POST http://localhost:8002/voice/offer",
        },
    }


# ── REST Chat API ─────────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    REST endpoint for the text chatbot.

    Browser sends: POST /api/chat
    Body: {session_id: "...", message: "user text"}

    - If session_id is null, a new session is created.
    - Conversation history is maintained per session_id.
    - Groq processes the message with MCP tool calling.
    - Returns: {session_id: "...", reply: "bot response"}
    """
    # Create or resume session
    session_id = req.session_id or str(uuid.uuid4())
    if session_id not in _chat_sessions:
        _chat_sessions[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        logger.info(f"New chat session: {session_id}")

    history = _chat_sessions[session_id]
    history.append({"role": "user", "content": req.message})

    client = AsyncGroq(api_key=config.groq_api_key)

    # Agentic loop — handles multi-step tool calling
    max_rounds = 6
    for _round in range(max_rounds):
        response = await client.chat.completions.create(
            model=config.groq_model,
            messages=history,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message
        history.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            # Final text response — done
            break

        # Execute each tool call and feed result back
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except Exception:
                arguments = {}

            logger.info(f"Chat tool call: {tool_name}({arguments})")
            tool_result = await _call_mcp_tool(tool_name, arguments)

            history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result),
            })

    reply = message.content or "Sorry, I couldn't generate a response. Please try again."
    logger.info(f"Chat reply [{session_id}]: {reply[:80]}...")
    return {"session_id": session_id, "reply": reply}


async def _call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Call MCP server and return result. Used by the REST chat endpoint."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 1,
        "params": {"name": tool_name, "arguments": arguments},
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(config.mcp_server_url, json=payload)
            resp.raise_for_status()
            return resp.json().get("result", {})
    except Exception as e:
        logger.error(f"MCP tool '{tool_name}' error: {e}")
        return {"error": "Could not reach the insurance backend. Please try again."}


# ── Chatbot Endpoint ──────────────────────────────────────────────────────────

@app.websocket("/chat")
async def chatbot_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for text chatbot.

    Browser connects to:  ws://localhost:8001/chat

    Each browser connection gets its own independent Pipecat pipeline.
    The pipeline runs for the lifetime of the WebSocket connection.
    When browser disconnects, the pipeline is cancelled.
    """
    await websocket.accept()
    client_host = websocket.client.host if websocket.client else "unknown"
    logger.info(f"New chat session from {client_host}")

    try:
        await run_chatbot(websocket)
    except WebSocketDisconnect:
        logger.info(f"Chat client {client_host} disconnected normally")
    except Exception as e:
        logger.error(f"Chat session error: {e}")
    finally:
        logger.info(f"Chat session for {client_host} cleaned up")


# ── Voice Bot Endpoints ───────────────────────────────────────────────────────

@app.post("/voice/offer")
async def voice_offer(offer: RTCOffer):
    """
    WebRTC offer endpoint for voice bot.

    Browser sends SDP offer to:  POST http://localhost:8001/voice/offer
    Server returns SDP answer.
    After handshake completes, audio streams flow via WebRTC.

    WebRTC handshake flow:
        1. Browser creates SDP offer (describes its audio capabilities)
        2. Browser POSTs offer to this endpoint
        3. Server creates SmallWebRTCConnection, processes offer
        4. Server returns SDP answer
        5. Browser and server exchange ICE candidates
        6. WebRTC connection established → voice bot pipeline starts
    """
    logger.info("Received WebRTC offer for voice bot")

    try:
        # Create a new WebRTC connection for this session
        connection = SmallWebRTCConnection()

        # Process the browser's SDP offer and generate our answer
        answer = await connection.initialize(
            offer={"sdp": offer.sdp, "type": offer.type}
        )

        # Store connection with its session ID for ICE candidate routing
        session_id = connection.session_id
        _voice_connections[session_id] = connection

        # Start the voice bot pipeline in background
        # This runs concurrently while WebRTC streams audio
        asyncio.create_task(
            _run_voice_session(connection, session_id)
        )

        logger.info(f"Voice session {session_id} started")
        return {
            "sdp": answer["sdp"],
            "type": answer["type"],
            "session_id": session_id,
        }

    except Exception as e:
        logger.error(f"Voice offer failed: {e}")
        return {"error": str(e)}, 500


@app.post("/voice/ice")
async def voice_ice(body: dict):
    """
    ICE candidate endpoint for voice bot WebRTC.

    Browser sends ICE candidates to:  POST http://localhost:8001/voice/ice
    These help the browser and server find the best network path for audio.
    """
    session_id = body.get("session_id")
    candidate = body.get("candidate")

    if not session_id or session_id not in _voice_connections:
        return {"error": "Session not found"}, 404

    connection = _voice_connections[session_id]
    await connection.add_ice_candidate(candidate)
    return {"status": "ok"}


async def _run_voice_session(connection: SmallWebRTCConnection, session_id: str):
    """Internal: run voice bot pipeline and clean up when done."""
    try:
        await run_voicebot(connection)
    except Exception as e:
        logger.error(f"Voice session {session_id} error: {e}")
    finally:
        _voice_connections.pop(session_id, None)
        logger.info(f"Voice session {session_id} cleaned up")


# ── Server Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info(f"Starting InsureFlow Bot Server on {config.host}:{config.port}")
    logger.info("Chat bot : ws://localhost:8002/chat")
    logger.info("Voice bot: POST http://localhost:8002/voice/offer")

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
    )

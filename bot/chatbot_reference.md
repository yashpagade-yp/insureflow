# InsureFlow Chatbot — Reference Code
# =====================================
# This file is a REFERENCE and EXPLANATION, not production code.
# Use this as a guide when building the actual InsureFlow chatbot.
#
# WHAT IS THIS?
# A text-based chatbot using Pipecat + Gemini.
# Customer types a message → Gemini reads it + decides which MCP tool to call
# → MCP tool calls backend API → Gemini replies in text → Customer reads the reply.
#
# DIFFERENCE FROM VOICE BOT:
#   Voice Bot  = Mic → STT → LLM → TTS → Speaker
#   Chat Bot   = Text Input → LLM → Text Output
#   (No audio. No Deepgram. No ElevenLabs. Just Gemini + WebSocket.)
#
# HOW TO RUN (after setup):
#   uv run chatbot.py
# =====================================

import os
from dotenv import load_dotenv
from loguru import logger

# ── Pipecat Core ──────────────────────────────────────────────────────────────
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.workers.runner import WorkerRunner

# ── LLM (Gemini) ──────────────────────────────────────────────────────────────
# For chatbot we use standard Gemini (NOT GeminiLive).
# GeminiLive = handles audio in real time (for voice bot)
# Gemini     = handles text messages (for chat bot)
from pipecat.services.google.llm import GoogleLLMService

# ── Conversation Context ───────────────────────────────────────────────────────
# LLMContext holds the full conversation history (all messages so far).
# LLMContextAggregator collects user messages and builds context for the LLM.
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContextAggregator

# ── Transport ──────────────────────────────────────────────────────────────────
# For chatbot we use WebSocket — lightweight, text-friendly.
# Customer browser connects here and sends/receives text messages.
from pipecat.transports.websocket.fastapi_websocket import FastAPIWebsocketTransport
from pipecat.transports.websocket.fastapi_websocket import FastAPIWebsocketParams

# ── Function Calling (MCP Tool Integration) ───────────────────────────────────
# This is how the LLM (Gemini) calls our MCP tools.
# We register Python functions here. Gemini decides when to call them.
from pipecat.services.llm_service import FunctionCallParams

load_dotenv(override=True)


# ==============================================================================
# SECTION 1: SYSTEM PROMPT
# ==============================================================================
# This is the most important part. This tells Gemini WHO it is and WHAT to do.
# For InsureFlow, this is the complete insurance journey guide.
# The actual system prompt is stored in system_prompt.py (see that file).

SYSTEM_PROMPT = """
You are InsureFlow, a friendly AI insurance assistant.
You help customers buy health, life, or general insurance step by step.

Follow this exact journey:
1. Ask for mobile number, insurance type, first name, last name
2. Call submit_insurance_form when you have all required details
3. Call send_login_otp with the mobile number
4. Ask customer for OTP and call verify_login_otp
5. Call get_quotes to fetch available plans
6. Present plans clearly and ask customer to choose one
7. Call select_plan when customer picks a plan
8. Ask about add-ons and call select_add_ons
9. Call create_payment to start payment
10. Call send_payment_otp to trigger OTP
11. Ask for payment OTP and call verify_payment_otp
12. Call list_user_policies to show the issued policy

RULES:
- Never make up policy numbers, premiums or quotes — always use tool results
- Ask one or two questions at a time, never dump all questions at once
- Be warm, clear and professional
- If a tool fails, apologize and offer to retry
"""


# ==============================================================================
# SECTION 2: MCP TOOL FUNCTIONS
# ==============================================================================
# These are Python wrapper functions that Pipecat exposes to Gemini as "tools".
# When Gemini decides to call submit_insurance_form, Pipecat runs this function.
# The function then calls our MCP Server, which calls the actual backend.
#
# HOW IT CONNECTS TO MCP:
#   Gemini decides → calls Python function below → function calls MCP server
#   MCP server → calls main_backend API → returns result → Gemini sees result
#
# NOTE: In production code, these will be in mcp_client.py and imported here.

import httpx

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")


async def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """
    Generic helper to call any tool on our MCP server.
    The MCP server is already running on port 8080.
    This sends a JSON-RPC request to the MCP server.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 1,
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(MCP_SERVER_URL, json=payload)
        resp.raise_for_status()
        result = resp.json()
        return result.get("result", {})


# ── Individual Tool Functions ──────────────────────────────────────────────────
# Each function below maps to one MCP tool we already built.
# Gemini calls these by name when it decides the time is right.

async def submit_insurance_form(params: FunctionCallParams):
    """Called when customer gives personal details. Submits form to backend."""
    result = await call_mcp_tool("submit_insurance_form", params.arguments)
    await params.result_callback(result)


async def send_login_otp(params: FunctionCallParams):
    """Called after form submission. Sends mock OTP to customer's mobile."""
    result = await call_mcp_tool("send_login_otp", params.arguments)
    await params.result_callback(result)


async def verify_login_otp(params: FunctionCallParams):
    """Called when customer provides OTP. Returns JWT token."""
    result = await call_mcp_tool("verify_login_otp", params.arguments)
    await params.result_callback(result)


async def get_quotes(params: FunctionCallParams):
    """Called after login. Fetches insurance quotes from provider_backend."""
    result = await call_mcp_tool("get_quotes", params.arguments)
    await params.result_callback(result)


async def select_plan(params: FunctionCallParams):
    """Called when customer picks a plan from the quotes."""
    result = await call_mcp_tool("select_plan", params.arguments)
    await params.result_callback(result)


async def select_add_ons(params: FunctionCallParams):
    """Called after plan selection. Saves chosen add-ons (or empty list)."""
    result = await call_mcp_tool("select_add_ons", params.arguments)
    await params.result_callback(result)


async def create_payment(params: FunctionCallParams):
    """Called when customer confirms payment. Creates payment session."""
    result = await call_mcp_tool("create_payment", params.arguments)
    await params.result_callback(result)


async def send_payment_otp(params: FunctionCallParams):
    """Called after payment creation. Sends payment OTP to mobile."""
    result = await call_mcp_tool("send_payment_otp", params.arguments)
    await params.result_callback(result)


async def verify_payment_otp(params: FunctionCallParams):
    """Called when customer provides payment OTP. Completes payment."""
    result = await call_mcp_tool("verify_payment_otp", params.arguments)
    await params.result_callback(result)


async def list_user_policies(params: FunctionCallParams):
    """Called after payment success. Shows customer their issued policy."""
    result = await call_mcp_tool("list_user_policies", params.arguments)
    await params.result_callback(result)


async def get_latest_incomplete_journey(params: FunctionCallParams):
    """Called for returning customer. Finds and resumes incomplete journey."""
    result = await call_mcp_tool("get_latest_incomplete_journey", params.arguments)
    await params.result_callback(result)


async def get_user_transactions(params: FunctionCallParams):
    """Called for returning customer. Lists all transactions."""
    result = await call_mcp_tool("get_user_transactions", params.arguments)
    await params.result_callback(result)


# ==============================================================================
# SECTION 3: TOOL DEFINITIONS FOR GEMINI
# ==============================================================================
# These tell Gemini WHAT each tool does and WHAT parameters to pass.
# Gemini reads these and decides when and how to call each tool.
# Format: OpenAI-style function schema (Pipecat standard).

TOOLS = [
    {
        "function_declarations": [
            {
                "name": "submit_insurance_form",
                "description": "Submit the insurance form to start a new customer journey. Call this when you have mobile_number, insurance_type, first_name, last_name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mobile_number": {"type": "string"},
                        "insurance_type": {"type": "string", "enum": ["health", "life", "general"]},
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "email": {"type": "string"},
                        "dob": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        "gender": {"type": "string", "enum": ["male", "female", "other"]},
                        "sum_insured": {"type": "number"},
                        "policy_term_years": {"type": "integer"},
                        "city": {"type": "string"},
                        "state": {"type": "string"},
                    },
                    "required": ["mobile_number", "insurance_type", "first_name", "last_name"],
                },
            },
            {
                "name": "send_login_otp",
                "description": "Send a mock OTP to the customer's mobile number for verification.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mobile_number": {"type": "string"},
                    },
                    "required": ["mobile_number"],
                },
            },
            {
                "name": "verify_login_otp",
                "description": "Verify the OTP entered by the customer. Returns JWT token on success.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mobile_number": {"type": "string"},
                        "otp": {"type": "string"},
                    },
                    "required": ["mobile_number", "otp"],
                },
            },
            {
                "name": "get_quotes",
                "description": "Fetch insurance quotes for the customer's transaction.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {"type": "string"},
                        "token": {"type": "string"},
                    },
                    "required": ["transaction_id", "token"],
                },
            },
            {
                "name": "select_plan",
                "description": "Save the customer's selected plan on the transaction.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {"type": "string"},
                        "selected_plan_id": {"type": "string"},
                        "token": {"type": "string"},
                    },
                    "required": ["transaction_id", "selected_plan_id", "token"],
                },
            },
            {
                "name": "select_add_ons",
                "description": "Save selected add-ons for the chosen plan. Pass empty list if no add-ons selected.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {"type": "string"},
                        "selected_plan_id": {"type": "string"},
                        "selected_add_ons": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "price": {"type": "number"},
                                },
                            },
                        },
                        "token": {"type": "string"},
                    },
                    "required": ["transaction_id", "selected_plan_id", "token"],
                },
            },
            {
                "name": "create_payment",
                "description": "Create a payment session for the transaction.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {"type": "string"},
                        "user_id": {"type": "string"},
                        "amount": {"type": "number"},
                        "token": {"type": "string"},
                    },
                    "required": ["transaction_id", "user_id", "amount", "token"],
                },
            },
            {
                "name": "send_payment_otp",
                "description": "Send a mock payment OTP to confirm payment.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "payment_reference": {"type": "string"},
                        "token": {"type": "string"},
                    },
                    "required": ["payment_reference", "token"],
                },
            },
            {
                "name": "verify_payment_otp",
                "description": "Verify payment OTP. On success, policy is auto-issued.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {"type": "string"},
                        "payment_reference": {"type": "string"},
                        "otp": {"type": "string"},
                        "token": {"type": "string"},
                    },
                    "required": ["transaction_id", "payment_reference", "otp", "token"],
                },
            },
            {
                "name": "list_user_policies",
                "description": "List all issued policies for the customer. Call after payment success.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "token": {"type": "string"},
                    },
                    "required": ["user_id", "token"],
                },
            },
            {
                "name": "get_latest_incomplete_journey",
                "description": "For returning customer — fetch their latest incomplete journey.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mobile_number": {"type": "string"},
                        "token": {"type": "string"},
                    },
                    "required": ["mobile_number", "token"],
                },
            },
            {
                "name": "get_user_transactions",
                "description": "List all transactions for the customer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "token": {"type": "string"},
                    },
                    "required": ["user_id", "token"],
                },
            },
        ]
    }
]


# ==============================================================================
# SECTION 4: PIPELINE (THE CHATBOT BRAIN)
# ==============================================================================
# This is the Pipecat pipeline for the chatbot.
# Flow: WebSocket Input → User Aggregator → Gemini LLM → WebSocket Output

async def run_chatbot(websocket):
    """
    Main chatbot function. Called when a browser connects via WebSocket.

    Pipeline flow:
        Browser types message
            ↓
        transport.input()         → receives text from WebSocket
            ↓
        user_context_aggregator   → adds message to conversation history
            ↓
        llm (Gemini)              → reads history, decides tool to call or responds
            ↓
        assistant_context_aggregator → saves Gemini response to history
            ↓
        transport.output()        → sends response text back to browser
    """

    # WebSocket Transport — text in, text out
    # In production, websocket comes from FastAPI endpoint
    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_out_enabled=False,   # No audio for chatbot
            add_wav_header=False,
            vad_enabled=False,         # No voice detection for chatbot
        ),
    )

    # Gemini LLM — the brain
    # api_key comes from .env file (GOOGLE_API_KEY)
    llm = GoogleLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.0-flash",      # Fast, capable model
    )

    # Register our MCP tool functions with Gemini
    # When Gemini decides to call "submit_insurance_form", this Python
    # function runs and calls our MCP server
    llm.register_function("submit_insurance_form", submit_insurance_form)
    llm.register_function("send_login_otp", send_login_otp)
    llm.register_function("verify_login_otp", verify_login_otp)
    llm.register_function("get_quotes", get_quotes)
    llm.register_function("select_plan", select_plan)
    llm.register_function("select_add_ons", select_add_ons)
    llm.register_function("create_payment", create_payment)
    llm.register_function("send_payment_otp", send_payment_otp)
    llm.register_function("verify_payment_otp", verify_payment_otp)
    llm.register_function("list_user_policies", list_user_policies)
    llm.register_function("get_latest_incomplete_journey", get_latest_incomplete_journey)
    llm.register_function("get_user_transactions", get_user_transactions)

    # Initial conversation — system prompt + first message
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Hello"},    # triggers first greeting
    ]

    # Context = full conversation history
    context = LLMContext(messages, tools=TOOLS)
    user_context_aggregator = OpenAILLMContextAggregator(context)
    assistant_context_aggregator = user_context_aggregator.assistant()

    # Build the pipeline
    pipeline = Pipeline(
        [
            transport.input(),             # 1. Receive text from browser
            user_context_aggregator,       # 2. Add to conversation history
            llm,                           # 3. Gemini thinks + maybe calls tool
            assistant_context_aggregator,  # 4. Save response to history
            transport.output(),            # 5. Send response back to browser
        ]
    )

    # Worker runs the pipeline
    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_connected(transport, client):
        logger.info("Chat client connected")

    @transport.event_handler("on_client_disconnected")
    async def on_disconnected(transport, client):
        logger.info("Chat client disconnected")
        await worker.cancel()

    runner = WorkerRunner(handle_sigint=False)
    await runner.add_workers(worker)
    await runner.run()


# ==============================================================================
# SECTION 5: FASTAPI SERVER (HOW BROWSER CONNECTS)
# ==============================================================================
# This is the HTTP server that:
#   - Serves the chatbot endpoint
#   - Accepts WebSocket connections from the browser
#   - Starts the chatbot pipeline per connection
#
# In production this will be in server.py

from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI(title="InsureFlow Chatbot Server")


@app.websocket("/chat")
async def chatbot_endpoint(websocket: WebSocket):
    """
    Browser connects to ws://localhost:8001/chat
    Each connection gets its own chatbot pipeline instance.
    """
    await websocket.accept()
    logger.info("New chat session started")
    await run_chatbot(websocket)


if __name__ == "__main__":
    # Start server on port 8001
    # (port 8000 = main_backend, port 8080 = MCP server, port 8001 = chatbot)
    uvicorn.run(app, host="0.0.0.0", port=8001)


# ==============================================================================
# SECTION 6: FRONTEND CONNECTION (HOW THE BROWSER TALKS TO THIS)
# ==============================================================================
# In ChatBot.jsx (React component in customer_app_frontend):
#
# const ws = new WebSocket("ws://localhost:8001/chat");
#
# ws.onmessage = (event) => {
#   const message = JSON.parse(event.data);
#   setChatMessages(prev => [...prev, { role: "bot", text: message.text }]);
# };
#
# const sendMessage = (text) => {
#   ws.send(JSON.stringify({ text }));
# };
#
# The browser connects → Pipecat pipeline starts →
# Customer types → Gemini reads → calls MCP tool → gets result → replies
# ==============================================================================


# ==============================================================================
# SECTION 7: WHAT IS DIFFERENT IN VOICE BOT
# ==============================================================================
# Chatbot (this file)        Voice Bot (voicebot_reference.py)
# ─────────────────────      ──────────────────────────────────
# Text input                 Mic input (WebRTC/Daily)
# Text output                Speaker output (WebRTC/Daily)
# GoogleLLMService           GeminiLiveLLMService
# No STT needed              Gemini Live handles STT internally
# No TTS needed              Gemini Live handles TTS internally
# FastAPIWebsocket           DailyTransport or SmallWebRTCTransport
# No VAD needed              SileroVADAnalyzer needed
# No animation               TalkingAnimation (robot avatar)
# Same MCP tools             Same MCP tools (no change)
# ==============================================================================

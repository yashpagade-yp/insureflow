"""
InsureFlow Chatbot Pipeline
==============================
Text-based chatbot using Pipecat + Groq LLM.

Flow:
    Browser (text input)
        ↓ WebSocket
    Pipecat pipeline
        ↓ User context aggregator (adds message to history)
        ↓ Groq LLM (reads history, calls MCP tool or responds)
        ↓ Assistant context aggregator (saves response to history)
        ↓ WebSocket
    Browser (text output)

Ports:
    main_backend : 8000
    mcp server   : 8080
    bot server   : 8001  ← this
    frontend     : 5173
"""

from loguru import logger

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.pipeline.runner import PipelineRunner

# Groq LLM — OpenAI-compatible, very fast inference
from pipecat.services.groq.llm import GroqLLMService

# Context management — OpenAI-compatible conversation context for Groq
from pipecat.processors.aggregators.llm_context import LLMContext

# WebSocket transport — text in, text out, no audio
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

from config import config
from system_prompt import SYSTEM_PROMPT
from mcp_client import TOOLS, register_tools


async def run_chatbot(websocket) -> None:
    """
    Main chatbot session function.
    Called once per browser connection. Each browser tab gets its own pipeline.

    Args:
        websocket: FastAPI WebSocket connection from the /chat endpoint in server.py
    """

    logger.info("Chatbot session started")

    # ── Transport ─────────────────────────────────────────────────────────────
    # WebSocket transport: receives text from browser, sends text back.
    # No audio processing — pure text conversation.
    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_out_enabled=False,   # No audio output for chatbot
            add_wav_header=False,
            vad_enabled=False,         # No voice activity detection for chatbot
        ),
    )

    # ── LLM ───────────────────────────────────────────────────────────────────
    # Groq with Llama 3.3 — fast enough for real-time chat, supports function calling.
    llm = GroqLLMService(
        api_key=config.groq_api_key,
        model=config.groq_model,
    )

    # Register all MCP tool functions — Groq will call these when needed
    register_tools(llm)

    # ── Conversation Context ───────────────────────────────────────────────────
    # OpenAILLMContext holds the full conversation history.
    # Initial messages: system prompt + first user message to trigger greeting.
    initial_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Hello, I'm here."},
    ]

    context = LLMContext(messages=initial_messages, tools=TOOLS)

    # create_context_aggregator gives us user + assistant aggregators in one call
    context_aggregator = llm.create_context_aggregator(context)

    # ── Pipeline ──────────────────────────────────────────────────────────────
    # The pipeline processes frames in order, left to right.
    # Each component passes frames to the next.
    pipeline = Pipeline(
        [
            transport.input(),                  # 1. Receive text frame from browser
            context_aggregator.user(),          # 2. Add user message to conversation history
            llm,                                # 3. Groq reads context → responds or calls tool
            context_aggregator.assistant(),     # 4. Save Groq's response to conversation history
            transport.output(),                 # 5. Send response text to browser
        ]
    )

    # ── Task + Runner ─────────────────────────────────────────────────────────
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    # ── Event Handlers ────────────────────────────────────────────────────────
    @transport.event_handler("on_client_connected")
    async def on_connected(transport, client):
        logger.info("Chat client connected")

    @transport.event_handler("on_client_disconnected")
    async def on_disconnected(transport, client):
        logger.info("Chat client disconnected — ending session")
        await task.cancel()

    # ── Run ───────────────────────────────────────────────────────────────────
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
    logger.info("Chatbot session ended")

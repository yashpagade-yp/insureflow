"""
InsureFlow Voice Bot Pipeline
================================
Real-time voice bot using Pipecat + Groq + Deepgram + Cartesia + Silero.

Flow:
    Browser (microphone)
        ↓ SmallWebRTC (audio stream)
    Pipecat pipeline
        ↓ Silero VAD (detects when customer stops talking)
        ↓ Deepgram STT (converts voice → text)
        ↓ User context aggregator (adds text to history)
        ↓ Groq LLM (reads history, calls MCP tool or responds)
        ↓ Assistant context aggregator (saves response to history)
        ↓ Cartesia TTS (converts text → voice)
        ↓ SmallWebRTC (audio stream)
    Browser (speaker)

Why each component:
    Silero VAD   — detects end of customer turn so bot knows when to respond
    Deepgram STT — converts customer voice to text (real-time, low latency)
    Groq LLM     — understands text, decides which MCP tool to call
    Cartesia TTS — converts bot response to natural-sounding voice
    SmallWebRTC  — browser audio transport (no Daily.co API key needed)
"""

from loguru import logger

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.pipeline.runner import PipelineRunner

# VAD — detects when customer stops speaking
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

# STT — converts voice to text
from pipecat.services.deepgram.stt import DeepgramSTTService

# LLM — Groq AI brain
from pipecat.services.groq.llm import GroqLLMService

# TTS — converts text response to voice
from pipecat.services.cartesia.tts import CartesiaTTSService

# Context management — OpenAI format (Groq is OpenAI-compatible)
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

# SmallWebRTC transport — browser WebRTC without needing Daily.co
from pipecat.transports.smallwebrtc.transport import (
    SmallWebRTCTransport,
    SmallWebRTCConnection,
    TransportParams,
)

from config import config
from system_prompt import SYSTEM_PROMPT
from mcp_client import TOOLS, register_tools


async def run_voicebot(webrtc_connection) -> None:
    """
    Main voice bot session function.
    Called once per browser connection from the /voice/offer endpoint in server.py.

    Args:
        webrtc_connection: SmallWebRTCConnection established during WebRTC handshake
    """

    logger.info("Voice bot session started")

    # ── Transport ─────────────────────────────────────────────────────────────
    # SmallWebRTC: real-time bidirectional audio via WebRTC.
    # audio_in_enabled  = receive customer's microphone
    # audio_out_enabled = send bot's voice to customer
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            # VAD is configured below and attached to user aggregator
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    stop_secs=0.8,   # Wait 0.8s of silence before considering turn ended
                )
            ),
        ),
    )

    # ── STT — Deepgram ────────────────────────────────────────────────────────
    # Converts customer's voice audio to text in real time.
    # model: "nova-2" — Deepgram's best model for English conversation
    stt = DeepgramSTTService(
        api_key=config.deepgram_api_key,
        model="nova-2",
        language="en-IN",   # English (India) — better for Indian accents
    )

    # ── LLM — Groq ────────────────────────────────────────────────────────────
    # Reads transcript, decides which MCP tool to call, generates spoken response.
    llm = GroqLLMService(
        api_key=config.groq_api_key,
        model=config.groq_model,
    )

    # Register all MCP tool functions — Groq calls them when needed
    register_tools(llm)

    # ── TTS — Cartesia ────────────────────────────────────────────────────────
    # Converts Groq's text response to natural-sounding voice audio.
    # Voice: "Sonic" — Cartesia's professional English voice
    tts = CartesiaTTSService(
        api_key=config.cartesia_api_key,
        voice_id=config.cartesia_voice_id,
        model_id="sonic-english",   # Cartesia's best English voice model
    )

    # ── Conversation Context ───────────────────────────────────────────────────
    # Initial messages: system prompt + trigger message for first greeting.
    initial_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Hello, I'm ready to speak with you.",
        },
    ]

    context = OpenAILLMContext(messages=initial_messages, tools=TOOLS)
    context_aggregator = llm.create_context_aggregator(context)

    # ── Pipeline ──────────────────────────────────────────────────────────────
    # Full voice pipeline: audio in → STT → LLM → TTS → audio out
    pipeline = Pipeline(
        [
            transport.input(),                  # 1. Receive audio from browser mic
            stt,                                # 2. Deepgram: audio → text
            context_aggregator.user(),          # 3. Add transcribed text to history
            llm,                                # 4. Groq: reads history → calls tool or responds
            tts,                                # 5. Cartesia: response text → voice audio
            transport.output(),                 # 6. Send audio to browser speaker
            context_aggregator.assistant(),     # 7. Save response to conversation history
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
        logger.info("Voice client connected")

    @transport.event_handler("on_client_disconnected")
    async def on_disconnected(transport, client):
        logger.info("Voice client disconnected — ending session")
        await task.cancel()

    # ── Run ───────────────────────────────────────────────────────────────────
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
    logger.info("Voice bot session ended")

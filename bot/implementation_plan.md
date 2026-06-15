# InsureFlow Bot — Implementation Plan
## Voice Bot + Chat Bot using Pipecat

---

## What We Are Building

A **Voice Bot** and **Chat Bot** for the InsureFlow customer journey.
The customer can either **speak** or **type** to complete the full insurance journey —
from form filling to policy issuance — without touching any form or button.

Both bots share the **same Pipecat pipeline core** and reuse the **same 14 MCP tools** already built.
Only the input/output layer differs (voice vs text).

---

## Architecture

```
VOICE BOT
─────────────────────────────────────────────────────────────────
Browser (Microphone)
    ↓  WebRTC (Daily.co)
Pipecat Server (Python)
    ↓  Silero VAD         → detects when customer stops talking
    ↓  Deepgram STT       → converts voice to text
    ↓  Gemini LLM         → understands + decides which MCP tool to call
    ↓  MCP Client         → calls our MCP Server (port 8080)
    ↓  MCP Server         → calls main_backend (port 8000)
    ↓  Cartesia TTS       → converts response text back to voice
    ↓  WebRTC (Daily.co)
Browser (Speaker) → Customer hears the bot speak

CHAT BOT
─────────────────────────────────────────────────────────────────
Browser (Text Input)
    ↓  WebSocket
Pipecat Server (Python)
    ↓  No STT, No VAD     → text goes directly to LLM
    ↓  Gemini LLM         → understands + decides which MCP tool to call
    ↓  MCP Client         → calls our MCP Server (port 8080)
    ↓  MCP Server         → calls main_backend (port 8000)
    ↓  No TTS             → text response goes back directly
    ↓  WebSocket
Browser (Chat UI) → Customer reads the response
```

---

## Connection Approach: Via MCP Server

We connect the bot through our **existing MCP Server (port 8080)** — not directly to the backend.

**Why:**
- 14 MCP tools are already built and tested
- Zero duplicate code — bot reuses everything
- Any MCP tool update automatically benefits the bot
- Clean separation of concerns

---

## Tech Stack

| Component       | Technology        | Purpose                                                  |
|-----------------|-------------------|----------------------------------------------------------|
| Bot Framework   | **Pipecat**       | Orchestrates the entire voice/chat pipeline              |
| Package Manager | **uv**            | Official Pipecat package manager (faster than pip)       |
| VAD             | **Silero**        | Detects when customer stops talking (voice bot only)     |
| STT             | **Deepgram**      | Speech → Text (voice bot only)                           |
| LLM             | **Groq**          | AI brain — understands customer, decides tool to call    |
| TTS             | **Cartesia**      | Text → Speech (voice bot only)                           |
| WebRTC          | **Daily.co**      | Real-time audio transport between browser and server     |
| WebSocket       | **FastAPI WS**    | Text transport for chat bot                              |
| MCP Client      | **mcp Python SDK**| Connects bot to our existing MCP server                  |
| Audio Encoding  | **Base64**        | Encodes audio bytes for WebSocket/WebRTC transport       |
| Frontend        | **Existing Vite** | Bot UI inside customer_app_frontend (existing folder)    |

---

## Why Groq for LLM?

- **Extremely fast** inference — lowest latency among all free LLMs
- Very generous **free tier** — no credit card required
- Supports **function calling** — needed for calling MCP tools
- Uses best open-source models: **Llama 3.3**, **Mixtral**, **Gemma**
- Perfect for real-time voice bot (speed is critical for natural conversation)

**Alternative free LLMs (if needed):**
- **Gemini** — Google's LLM, free tier via AI Studio
- **Ollama** — completely free, runs fully locally, no API key needed

---

## Why Cartesia for TTS?

- Official Pipecat quickstart uses Cartesia
- Better latency than ElevenLabs for real-time voice
- More affordable for production usage
- Natively supported as a Pipecat extra

---

## Why Silero VAD?

VAD (Voice Activity Detection) is critical for the voice bot.
Without it, the bot cannot know when the customer has finished speaking.

**InsureFlow example:**
```
Customer: "I want health insurance for my family."
              ↑ speaking...                        ↑ silence detected by Silero
                                                   → Deepgram converts to text
                                                   → Gemini responds
```

Without VAD: Bot would either interrupt the customer or never respond.
With VAD: Natural turn-based conversation, just like a real phone call.

---

## Installation Command

```bash
uv add "pipecat-ai[daily,deepgram,groq,cartesia,silero]"
```

| Extra      | What It Installs            |
|------------|-----------------------------|
| `daily`    | Daily.co WebRTC transport   |
| `deepgram` | Deepgram STT service        |
| `groq`     | Groq LLM service            |
| `cartesia` | Cartesia TTS service        |
| `silero`   | Silero VAD analyzer         |

---

## API Keys Required

| Key                  | Service     | Where Used                         |
|----------------------|-------------|-------------------------------------|
| `GROQ_API_KEY`       | Groq        | LLM — AI brain                      |
| `DEEPGRAM_API_KEY`   | Deepgram    | STT — voice to text                 |
| `CARTESIA_API_KEY`   | Cartesia    | TTS — text to voice                 |
| `DAILY_API_KEY`      | Daily.co    | WebRTC — audio transport            |
| `MCP_SERVER_URL`     | Our MCP     | `http://localhost:8080/mcp`         |

**Status: Pending — user will provide after plan approval.**

---

## System Prompt (Bot Brain Instructions)

The system prompt tells Gemini exactly who it is and how to follow the InsureFlow journey.
This is the most critical configuration — a bad system prompt = a broken bot.

```
You are InsureFlow, a friendly and professional AI insurance assistant.
You help customers buy health, life, or general insurance in India through
a step-by-step guided conversation.

IMPORTANT: Your output will be spoken aloud (voice) or shown as chat text.
Keep responses clear, concise, and conversational. Never use markdown,
bullet points, or special characters in voice responses.

CUSTOMER JOURNEY — FOLLOW THIS EXACTLY:

STEP 1: COLLECT FORM DETAILS (No auth needed)
  - Greet the customer warmly
  - Ask for mobile number, then insurance type (health/life/general)
  - Ask for first name and last name
  - Optionally ask: email, date of birth (YYYY-MM-DD), gender
  - Optionally ask: sum insured amount, policy term in years, city, state
  - Once you have mobile, insurance_type, first_name, last_name → call submit_insurance_form
  - Say: "Your details are saved. Let me send an OTP to your mobile."

STEP 2: OTP VERIFICATION
  - Call send_login_otp with the customer's mobile number
  - Ask: "Please tell me the OTP you received on your mobile."
  - When customer gives OTP → call verify_login_otp
  - Store the token and user_id from the response — you will need these throughout
  - Say: "Mobile verified! Let me fetch the best insurance plans for you."

STEP 3: SHOW QUOTES
  - Call get_quotes with transaction_id (from Step 1 response) and token
  - Read out available plans clearly, one by one:
    "I found [N] plans. Plan 1: [Company], [Plan Name], [Premium] rupees per year,
     coverage of [Amount] rupees. Plan 2: ..."
  - Ask: "Which plan would you like to choose?"

STEP 4: SELECT PLAN
  - When customer names a plan or number → call select_plan
  - Say: "Great choice! This plan has some optional add-ons."
  - If add-ons exist → read them out and ask if customer wants any
  - Call select_add_ons (with selected add-ons or empty list)

STEP 5: PAYMENT
  - Tell the customer the total amount
  - Ask: "Shall I go ahead with the payment?"
  - If yes → call create_payment, then call send_payment_otp
  - Say: "Payment OTP sent to your mobile. Please tell me the OTP."
  - When customer gives OTP → call verify_payment_otp

STEP 6: POLICY ISSUED
  - Call list_user_policies to fetch the issued policy
  - Say: "Congratulations! Your policy is issued. Policy Number: [number].
    Company: [name], Plan: [name], Coverage: [amount] rupees,
    Premium: [amount] rupees per year."

RETURNING CUSTOMER JOURNEY:
  - If customer says they already have an account or want to check status:
    → Ask for mobile number
    → Call send_login_otp → verify_login_otp
    → Ask: "Do you want to see your policies, check transaction status,
             or resume an incomplete journey?"
    → Call the appropriate tool based on their choice

RULES:
  - Always be polite, clear, and patient
  - Ask one or two questions at a time — never ask everything at once
  - If a tool fails, say sorry and offer to retry
  - Never make up quotes, plan names, premiums, or policy numbers
  - Always use real values from tool responses
  - Remember transaction_id, token, user_id, payment_reference across the conversation
  - For voice: speak naturally, no symbols, no markdown
  - For chat: you may use simple formatting
```

---

## Folder Structure to Build

```
bot/
├── implementation_plan.md       ← this file
├── README.md                    ← setup and run guide
├── chatbot_reference.py         ← reference code with explanations
├── voicebot_reference.py        ← reference code from Pipecat docs
├── requirements.txt             ← pipecat-ai + extras
├── .env.example                 ← API key placeholders
├── config.py                    ← loads env vars
├── system_prompt.py             ← InsureFlow system prompt for Gemini
├── mcp_client.py                ← connects to MCP server, wraps tools
├── pipeline_voice.py            ← Pipecat voice pipeline
├── pipeline_chat.py             ← Pipecat chat pipeline
└── server.py                    ← FastAPI server (voice + chat endpoints)

frontend/customer_app_frontend/src/bot/
├── VoiceBot.jsx                 ← mic button + WebRTC UI
└── ChatBot.jsx                  ← text input + WebSocket chat UI
```

---

## MCP Tools Used by the Bot

| Customer Action               | MCP Tool Called                      |
|-------------------------------|--------------------------------------|
| Gives personal details        | `submit_insurance_form`              |
| Receive OTP                   | `send_login_otp`                     |
| Enters OTP                    | `verify_login_otp`                   |
| Asks for plans                | `get_quotes`                         |
| Picks a plan                  | `select_plan`                        |
| Picks add-ons                 | `select_add_ons`                     |
| Proceeds to payment           | `create_payment`                     |
| Payment OTP triggered         | `send_payment_otp`                   |
| Enters payment OTP            | `verify_payment_otp`                 |
| Policy issued — show it       | `list_user_policies`                 |
| Returning customer login      | `send_login_otp` + `verify_login_otp`|
| Check transactions            | `get_user_transactions`              |
| Resume journey                | `get_latest_incomplete_journey`      |

**Zero new tools needed. All 14 MCP tools reused as-is.**

---

## Port Map (All Services)

| Service            | Port  |
|--------------------|-------|
| main_backend       | 8000  |
| MCP Server         | 8080  |
| Bot Server         | 8001  |
| Frontend (Vite)    | 5173  |

---

## Build Steps Checklist

- [ ] Install `uv` package manager
- [ ] Create `bot/requirements.txt` (or pyproject.toml for uv)
- [ ] Create `bot/.env.example` with all key placeholders
- [ ] Create `bot/config.py` — loads all API keys
- [ ] Create `bot/system_prompt.py` — full Gemini instructions
- [ ] Create `bot/mcp_client.py` — wraps MCP tools for Pipecat
- [ ] Create `bot/pipeline_voice.py` — Deepgram + Gemini + Cartesia + Silero
- [ ] Create `bot/pipeline_chat.py` — Gemini + WebSocket text
- [ ] Create `bot/server.py` — FastAPI with /voice and /chat endpoints
- [ ] Create `VoiceBot.jsx` in customer frontend
- [ ] Create `ChatBot.jsx` in customer frontend
- [ ] Add bot section to existing frontend navigation
- [ ] Test voice flow end to end
- [ ] Test chat flow end to end

---

## What Is NOT Needed

- No new backend routes
- No new MCP tools
- No new database models
- No changes to CLI or existing MCP server code

---

## Pending From You

- `GROQ_API_KEY`
- `DEEPGRAM_API_KEY`
- `CARTESIA_API_KEY`
- `DAILY_API_KEY`

These will go into `bot/.env` when provided.

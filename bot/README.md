# InsureFlow Bot

Voice Bot and Chat Bot for the InsureFlow customer journey, built with Pipecat.

---

## What This Bot Does

The bot guides insurance customers through the complete journey using natural conversation:

- Customer **speaks** (Voice Bot) or **types** (Chat Bot)
- Bot collects details, fetches quotes, helps select a plan, processes payment
- Policy is issued at the end — all through conversation, no forms

Supports both:
- **New Customer** — full journey from form to policy
- **Returning Customer** — login, view policies, resume incomplete journey

---

## Tech Stack

| Component     | Technology  |
|---------------|-------------|
| Framework     | Pipecat     |
| `GROQ_API_KEY`       | Groq        | LLM — AI brain                      |
| `DEEPGRAM_API_KEY`   | Deepgram    | STT — voice to text                 |
| `CARTESIA_API_KEY`   | Cartesia    | TTS — text to voice                 |
| `DAILY_API_KEY`      | Daily.co    | WebRTC — audio transport            |
| VAD           | Silero      |
| MCP Tools     | Our existing MCP server (port 8080) |

---

## Prerequisites

- Python 3.11 or higher
- `uv` package manager installed
- All backend services running:
  - `main_backend` on port 8000
  - `mcp` server on port 8080

### Install uv

```bash
pip install uv
```

---

## Setup

### 1. Clone and go to the bot folder

```bash
cd insurance/bot
```

### 2. Install dependencies

```bash
uv add "pipecat-ai[daily,deepgram,groq,cartesia,silero]"
```

### 3. Set up environment variables

Copy the example file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
CARTESIA_API_KEY=your_cartesia_api_key_here
DAILY_API_KEY=your_daily_api_key_here
MCP_SERVER_URL=http://localhost:8080/mcp
```

### 4. Start the bot server

```bash
uv run server.py
```

Bot server will start on **port 8001**.

---

## API Keys — Where to Get Them

| Key | Service | Free Tier |
|-----|---------|-----------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com/) | Yes — very generous |
| `DEEPGRAM_API_KEY` | [console.deepgram.com](https://console.deepgram.com/) | Yes — $200 credit |
| `CARTESIA_API_KEY` | [play.cartesia.ai](https://play.cartesia.ai/) | Yes — free tier |
| `DAILY_API_KEY` | [dashboard.daily.co](https://dashboard.daily.co/) | Yes — free tier |

---

## Folder Structure

```
bot/
├── README.md                ← you are here
├── implementation_plan.md   ← full technical plan
├── chatbot_reference.py     ← chatbot reference code with explanations
├── .env.example             ← API key template
├── config.py                ← loads environment variables
├── system_prompt.py         ← Gemini system prompt (insurance journey)
├── mcp_client.py            ← connects to MCP server, wraps tools for Pipecat
├── pipeline_voice.py        ← Voice bot pipeline (Deepgram + Gemini + Cartesia)
├── pipeline_chat.py         ← Chat bot pipeline (Gemini + WebSocket)
└── server.py                ← FastAPI server with /voice and /chat endpoints
```

---

## How It Works

### Voice Bot

```
Customer speaks into browser mic
    ↓
Daily.co WebRTC sends audio to Pipecat server
    ↓
Silero VAD detects when customer stops talking
    ↓
Deepgram STT converts audio → text
    ↓
Gemini LLM reads text, decides what to do
    ↓
Pipecat calls MCP tool (e.g. get_quotes)
    ↓
MCP server calls main_backend API
    ↓
Result returned to Gemini
    ↓
Gemini generates spoken response
    ↓
Cartesia TTS converts text → voice
    ↓
Daily.co sends audio back to browser
    ↓
Customer hears the bot speak
```

### Chat Bot

```
Customer types a message in browser
    ↓
WebSocket sends text to Pipecat server
    ↓
Gemini LLM reads text, decides what to do
    ↓
Pipecat calls MCP tool (e.g. submit_insurance_form)
    ↓
MCP server calls main_backend API
    ↓
Result returned to Gemini
    ↓
Gemini generates text response
    ↓
WebSocket sends text back to browser
    ↓
Customer reads the response
```

---

## Port Map

| Service        | Port |
|----------------|------|
| main_backend   | 8000 |
| MCP server     | 8080 |
| Bot server     | 8001 |
| Frontend       | 5173 |

---

## MCP Tools Used

The bot uses these existing tools — no new tools needed:

| Journey Step            | Tool Called                     |
|-------------------------|---------------------------------|
| Submit form             | `submit_insurance_form`         |
| Send login OTP          | `send_login_otp`                |
| Verify login OTP        | `verify_login_otp`              |
| Fetch quotes            | `get_quotes`                    |
| Select plan             | `select_plan`                   |
| Select add-ons          | `select_add_ons`                |
| Create payment          | `create_payment`                |
| Send payment OTP        | `send_payment_otp`              |
| Verify payment OTP      | `verify_payment_otp`            |
| View policy             | `list_user_policies`            |
| View transactions       | `get_user_transactions`         |
| Resume journey          | `get_latest_incomplete_journey` |

---

## Frontend Integration

The bot UI is part of the existing `customer_app_frontend` (Vite + React):

- `VoiceBot.jsx` — microphone button, WebRTC connection, real-time audio
- `ChatBot.jsx` — chat input box, WebSocket connection, message display

Both components are inside `frontend/customer_app_frontend/src/bot/`.

---

## Status

| Item               | Status         |
|--------------------|----------------|
| Implementation plan| Done           |
| Reference code     | Done           |
| API keys           | Pending        |
| Bot server         | Not started    |
| Voice pipeline     | Not started    |
| Chat pipeline      | Not started    |
| Frontend UI        | Not started    |

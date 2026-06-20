# Docker Implementation Plan

This file tracks the Dockerization work for the InsureFlow project step by step.

## Current Scope

- Phase 1 includes:
  - `main_backend`
  - `provider_backend`
  - external MongoDB cluster
- Phase 2 includes:
  - `mcp`
  - `bot`

## Progress Checklist

- [x] Create a separate Docker branch
  - Branch selected: `Feature Dockerize Project`
- [x] Confirm Docker Desktop is installed
- [x] Confirm `.env` files already exist
- [x] Decide Docker phase 1 scope
  - Scope selected: `main_backend + provider_backend + MongoDB cluster`
- [x] Decide to keep `bot` and `mcp` for later
- [x] Fix local `main_backend` startup blocker before Dockerization
  - Replaced incompatible union-style type annotations in `calling_bot_model.py`
- [x] Inspect both backends for exact run commands, ports, and environment variable usage
  - Both backends start with `python -m uvicorn main:app --host 0.0.0.0 --port <port>`
  - `main_backend` listens on `8000`
  - `provider_backend` listens on `8001`
- [x] Verify how both backends connect to the MongoDB cluster
  - Both backends read `MONGO_URI` from their own `.env` files
  - `main_backend` reads `MAIN_DB_NAME`
  - `provider_backend` reads `PROVIDER_DB_NAME`
- [x] Finalize the Docker structure for phase 1
  - Phase 1 runs two backend containers and keeps MongoDB external
- [x] Create Dockerfile for `backend/main_backend`
- [x] Create Dockerfile for `backend/provider_backend`
- [x] Create `.dockerignore` files for both backends
- [x] Create `docker-compose.yml` for phase 1
- [x] Wire Compose with backend environment variables
  - `docker-compose.yml` uses each backend `.env` file
  - Compose injects `PROVIDER_BACKEND_URL=http://provider_backend:8001` for container networking
- [x] Build Docker images
- [x] Run both backend containers
- [x] Test backend startup and API flow
  - `http://localhost:8000/health` returned status OK
  - `http://localhost:8001/health` returned status OK
- [x] Fix first Docker runtime blocker after initial container start
  - Added missing `pymongo`, `PyJWT`, and `passlib[bcrypt]` to `backend/main_backend/requirements.txt`
- [ ] Fix Docker-related issues if found
- [x] Mark Docker phase 1 complete

## Phase 2 Checklist

- [x] Inspect both frontends for exact build flow, ports, and environment variable usage
  - Both frontends are Vite apps built with `npm run build`
  - `customer_app_frontend` uses `VITE_MAIN_API_BASE_URL`
  - `provider_app_frontend` uses `VITE_PROVIDER_API_BASE_URL`
- [x] Finalize the Docker structure for phase 2
  - Frontends are built with Node and served by Nginx
  - Nginx is configured with SPA fallback for React Router
- [x] Create Dockerfile for `frontend/customer_app_frontend`
- [x] Create Dockerfile for `frontend/provider_app_frontend`
- [x] Create frontend `.dockerignore` files
- [x] Add SPA Nginx config for both frontends
- [x] Extend `docker-compose.yml` with frontend services
- [x] Wire frontend build-time API base URLs
- [x] Build frontend Docker images
- [x] Run frontend containers
- [x] Test both frontend routes in the browser
  - `http://localhost:3000` returned HTTP 200
  - `http://localhost:3001` returned HTTP 200
  - `http://localhost:8000/health` returned status OK
  - `http://localhost:8001/health` returned status OK
- [x] Mark Docker phase 2 complete
  - Customer bot-related pages still depend on phase 3 services (`bot` on port `8002`)

## Phase 3 Checklist

- [x] Inspect `mcp`, `bot`, and customer bot-related frontend pages
- [x] Fix phase-3 configuration gaps before Docker build
  - `mcp/config.py` now supports environment variables
  - customer bot pages now read `VITE_BOT_BASE_URL`
  - `bot/requirements.txt` now includes the MCP client dependency
- [x] Create Dockerfile for `mcp`
- [x] Create `.dockerignore` for `mcp`
- [x] Create Dockerfile for `bot`
- [x] Create `.dockerignore` for `bot`
- [x] Extend frontend build config for bot URL injection
- [x] Extend `docker-compose.yml` with `mcp` and `bot`
- [x] Build phase 3 Docker images
- [x] Run full six-service stack
- [x] Test `mcp`, `bot`, and customer bot-related browser paths
  - `http://localhost:8080/mcp` responded from the MCP server
  - `http://localhost:8002` returned bot health JSON
  - `POST http://localhost:8002/api/chat` returned a live assistant reply
  - `http://localhost:3000` returned HTTP 200 after customer frontend rebuild
- [x] Fix first phase-3 bot runtime blocker
  - Replaced the unsupported `smallwebrtc` Pipecat extra with `webrtc` in `bot/requirements.txt`
- [x] Fix second phase-3 bot runtime blocker
  - Updated `bot/chatbot.py` and `bot/voicebot.py` to use Pipecat's current `LLMContext` import path
- [x] Fix third phase-3 bot runtime blocker
  - Added required OpenCV system libraries to `bot/Dockerfile`
- [x] Mark Docker phase 3 complete

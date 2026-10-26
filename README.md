# Market Insight

AI-powered stock market research starter using FastAPI, yfinance, and React.

## Features
- Stock quote, company overview, and historical prices
- Responsive React dashboard with price chart
- FastAPI interactive docs and health check
- Environment configuration; no API secrets committed

## Requirements
Python 3.10+, Node.js 20+, and internet access for Yahoo Finance data.

## Start backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

## Start frontend (second terminal)
```bash
cd frontend
npm install
npm run dev
```
Open the URL printed by Vite, normally http://localhost:5173.

## Endpoints
- `GET /api/health`
- `GET /api/stock/{symbol}/quote`
- `GET /api/stock/{symbol}/history?period=1mo&interval=1d`
- `GET /api/stock/{symbol}/overview`

**Disclaimer:** Educational research only, not personalized financial advice. Market data may be delayed, incomplete, or unavailable. No predictions or returns are guaranteed.


## AI research assistant (local model)

The AI assistant uses a LangGraph workflow and streams its response to the React UI using Server-Sent Events. It retrieves a small Yahoo Finance snapshot before answering. If the local model is unavailable, the endpoint falls back to a clearly labeled data snapshot.

1. Install [Ollama](https://ollama.com/) and start the Ollama service.
2. Pull a small local model, for example:
   ```bash
   ollama pull qwen2.5:3b
   ```
3. Install the backend requirements again: `pip install -r requirements.txt`.
4. Optional environment variables: `OLLAMA_MODEL=qwen2.5:3b` and `OLLAMA_BASE_URL=http://localhost:11434`.
5. Restart FastAPI. Check `GET /api/assistant/health` and use the Research assistant panel in the dashboard.

Chat endpoint: `POST /api/assistant/chat` with JSON `{"symbol":"AAPL","question":"Summarize recent price action"}`; it returns an SSE stream. The local model runs on your own machine; no paid AI API key is required. For Docker or remote deployments, configure `OLLAMA_BASE_URL` to a reachable Ollama server.

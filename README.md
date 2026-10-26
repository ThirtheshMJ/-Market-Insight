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

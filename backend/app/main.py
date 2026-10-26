import math
import re
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf

app = FastAPI(title="Market Insight API", version="0.1.0",
              description="Market data API for the Market Insight research platform.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False, allow_methods=["GET"], allow_headers=["*"]
)
SYMBOL_RE = re.compile(r"^[A-Za-z0-9.^=_-]{1,20}$")
PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"}
INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"}

def symbol_or_422(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not SYMBOL_RE.fullmatch(symbol):
        raise HTTPException(422, "Invalid ticker symbol format.")
    return symbol

def num(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "market-insight-api"}

@app.get("/api/stock/{symbol}/quote")
def quote(symbol: str):
    symbol = symbol_or_422(symbol)
    try:
        ticker = yf.Ticker(symbol)
        fast = ticker.fast_info
        price, previous = num(fast.get("last_price")), num(fast.get("previous_close"))
        try:
            info = ticker.get_info()
        except Exception:
            info = {}
        if price is None and not info:
            raise HTTPException(502, "No quote data returned. Check the ticker and try again.")
        change = price - previous if price is not None and previous is not None else None
        return {
            "symbol": symbol, "name": info.get("longName") or info.get("shortName") or symbol,
            "currency": fast.get("currency"), "exchange": fast.get("exchange"),
            "price": price, "previous_close": previous, "change": change,
            "change_percent": change / previous * 100 if change is not None and previous else None
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, "Market data temporarily unavailable.") from exc

@app.get("/api/stock/{symbol}/history")
def history(symbol: str, period: str = Query("1mo"), interval: str = Query("1d")):
    symbol = symbol_or_422(symbol)
    if period not in PERIODS:
        raise HTTPException(422, f"Unsupported period. Choose: {', '.join(sorted(PERIODS))}")
    if interval not in INTERVALS:
        raise HTTPException(422, f"Unsupported interval. Choose: {', '.join(sorted(INTERVALS))}")
    try:
        frame = yf.Ticker(symbol).history(period=period, interval=interval)
        if frame.empty:
            raise HTTPException(502, "No historical data returned for this ticker and range.")
        points = []
        for stamp, row in frame.iterrows():
            volume = num(row.get("Volume"))
            points.append({"date": stamp.isoformat(), "open": num(row.get("Open")),
                           "high": num(row.get("High")), "low": num(row.get("Low")),
                           "close": num(row.get("Close")),
                           "volume": int(volume) if volume is not None else None})
        return {"symbol": symbol, "period": period, "interval": interval, "points": points}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, "Historical market data temporarily unavailable.") from exc

@app.get("/api/stock/{symbol}/overview")
def overview(symbol: str):
    symbol = symbol_or_422(symbol)
    try:
        info = yf.Ticker(symbol).get_info()
        if not info:
            raise HTTPException(502, "No company overview returned for this ticker.")
        return {
            "symbol": symbol, "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector"), "industry": info.get("industry"),
            "website": info.get("website"), "summary": info.get("longBusinessSummary"),
            "market_cap": info.get("marketCap"), "trailing_pe": num(info.get("trailingPE")),
            "dividend_yield": num(info.get("dividendYield")),
            "fifty_two_week_high": num(info.get("fiftyTwoWeekHigh")),
            "fifty_two_week_low": num(info.get("fiftyTwoWeekLow"))
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, "Company information temporarily unavailable.") from exc

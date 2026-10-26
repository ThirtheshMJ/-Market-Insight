"""LangGraph-powered research assistant with an optional local Ollama model."""
import asyncio
import json
import os
from typing import TypedDict, AsyncIterator

import yfinance as yf
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

router = APIRouter(prefix="/api/assistant", tags=["AI research assistant"])

class AssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    symbol: str = Field(default="AAPL", min_length=1, max_length=20)

class ResearchState(TypedDict, total=False):
    question: str
    symbol: str
    context: str
    answer: str

def market_context(symbol: str) -> str:
    """Retrieve a small, current snapshot from Yahoo Finance for grounding."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.get_info() or {}
        fast = ticker.fast_info
        price = fast.get("last_price")
        previous = fast.get("previous_close")
        history = ticker.history(period="1mo", interval="1d")
        closes = history["Close"].dropna() if not history.empty else []
        recent = [round(float(x), 2) for x in closes.tail(5).tolist()] if len(closes) else []
        return json.dumps({
            "symbol": symbol,
            "company": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": fast.get("currency"),
            "last_available_price": float(price) if price is not None else None,
            "previous_close": float(previous) if previous is not None else None,
            "market_cap": info.get("marketCap"),
            "trailing_pe": info.get("trailingPE"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "recent_daily_closes": recent,
            "business_summary": (info.get("longBusinessSummary") or "")[:1200],
            "source": "yfinance / Yahoo Finance; values may be delayed"
        }, default=str)
    except Exception as exc:
        return json.dumps({"symbol": symbol, "data_note": f"Market context unavailable: {type(exc).__name__}"})

def make_graph():
    async def retrieve_node(state: ResearchState) -> ResearchState:
        return {"context": await asyncio.to_thread(market_context, state["symbol"])}

    async def answer_node(state: ResearchState) -> ResearchState:
        question = state["question"]
        context = state.get("context", "{}")
        model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            from langchain_ollama import ChatOllama
            llm = ChatOllama(model=model_name, base_url=base_url, temperature=0.2)
            prompt = (
                "You are Market Insight, a cautious financial research assistant. "
                "Use the supplied market snapshot as context, not as guaranteed real-time data. "
                "Explain assumptions and uncertainty. Do not give personalized investment instructions, "
                "promise returns, or fabricate missing figures. State that this is educational information, "
                "not financial advice. Keep the answer useful and structured.\n\n"
                f"Ticker: {state['symbol']}\nMarket snapshot JSON: {context}\n"
                f"User question: {question}"
            )
            chunks = []
            async for chunk in llm.astream(prompt):
                text = getattr(chunk, "content", "")
                if isinstance(text, str):
                    chunks.append(text)
                elif isinstance(text, list):
                    chunks.extend(part.get("text", "") for part in text if isinstance(part, dict))
            answer = "".join(chunks).strip()
            if answer:
                return {"answer": answer}
        except Exception:
            pass
        try:
            data = json.loads(context)
        except Exception:
            data = {}
        price = data.get("last_available_price")
        prev = data.get("previous_close")
        change = ((price - prev) / prev * 100) if isinstance(price, (int, float)) and isinstance(prev, (int, float)) and prev else None
        fallback = [
            f"## Research snapshot: {state['symbol']}",
            f"**Company:** {data.get('company') or state['symbol']}",
            f"**Sector / industry:** {data.get('sector') or 'Not available'} / {data.get('industry') or 'Not available'}",
            f"**Last available price:** {price if price is not None else 'Not available'} {data.get('currency') or ''}",
            f"**Change vs. previous close:** {f'{change:+.2f}%' if change is not None else 'Not available'}",
            f"**Market cap:** {data.get('market_cap') or 'Not available'}",
            f"**Trailing P/E:** {data.get('trailing_pe') or 'Not available'}",
            "",
            f"**Your question:** {question}",
            "",
            "The local AI model is not reachable, so this is a data snapshot rather than a generated AI interpretation. "
            "To enable the full assistant, install Ollama, pull the configured model, and start the Ollama service. "
            "The API will continue to work without it.",
            "",
            "**Research checklist:** compare recent earnings and guidance, cash flow, valuation against peers, "
            "major risks, and your investment time horizon. A single price snapshot is not enough to make a decision.",
            "",
            "*Educational research only; not personalized financial advice.*"
        ]
        return {"answer": "\n".join(fallback)}

    graph = StateGraph(ResearchState)
    graph.add_node("retrieve_market_context", retrieve_node)
    graph.add_node("research_answer", answer_node)
    graph.set_entry_point("retrieve_market_context")
    graph.add_edge("retrieve_market_context", "research_answer")
    graph.add_edge("research_answer", END)
    return graph.compile()

research_graph = make_graph()

@router.get("/health")
async def assistant_health():
    return {
        "status": "ok",
        "graph": "LangGraph",
        "provider": "Ollama local model",
        "model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "note": "The assistant falls back to a market snapshot if the local model is unavailable."
    }

@router.post("/chat")
async def assistant_chat(payload: AssistantRequest):
    symbol = payload.symbol.strip().upper()
    if not all(ch.isalnum() or ch in ".^=_-" for ch in symbol):
        raise HTTPException(status_code=422, detail="Invalid ticker symbol.")

    async def events() -> AsyncIterator[str]:
        yield "event: status\\ndata: " + json.dumps({"message": "Retrieving market context..."}) + "\\n\\n"
        emitted_model_tokens = False
        full_answer = ""
        try:
            async for event in research_graph.astream_events(
                {"question": payload.question.strip(), "symbol": symbol},
                version="v2"
            ):
                if event.get("event") == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    text = getattr(chunk, "content", "")
                    if isinstance(text, str) and text:
                        emitted_model_tokens = True
                        full_answer += text
                        yield "event: token\\ndata: " + json.dumps({"text": text}) + "\\n\\n"
                    elif isinstance(text, list):
                        for part in text:
                            piece = part.get("text", "") if isinstance(part, dict) else ""
                            if piece:
                                emitted_model_tokens = True
                                full_answer += piece
                                yield "event: token\\ndata: " + json.dumps({"text": piece}) + "\\n\\n"
                elif event.get("event") == "on_chain_end" and event.get("name") == "LangGraph":
                    pass
            # If Ollama isn't available, the graph intentionally returns a useful
            # snapshot fallback. Deliver that fallback progressively as SSE chunks.
            if not emitted_model_tokens:
                result = await research_graph.ainvoke({
                    "question": payload.question.strip(),
                    "symbol": symbol
                })
                answer = result.get("answer", "No answer was produced.")
                for offset in range(0, len(answer), 28):
                    yield "event: token\\ndata: " + json.dumps({"text": answer[offset:offset + 28]}) + "\\n\\n"
                    await asyncio.sleep(0.01)
            yield "event: done\\ndata: " + json.dumps({"ok": True, "symbol": symbol}) + "\\n\\n"
        except Exception as exc:
            yield "event: error\\ndata: " + json.dumps({"message": f"Assistant request failed: {type(exc).__name__}"}) + "\\n\\n"
        yield "event: close\\ndata: {}\\n\\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"
    })

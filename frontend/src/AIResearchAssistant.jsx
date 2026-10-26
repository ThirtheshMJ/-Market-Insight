import { useState } from "react";
import { BrainCircuit, Send, LoaderCircle, Sparkles } from "lucide-react";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function AIResearchAssistant({ symbol = "AAPL" }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function ask(text = question) {
    const prompt = text.trim();
    if (!prompt || busy) return;
    setQuestion("");
    setError("");
    setMessages(old => [...old, { role: "user", text: prompt }, { role: "assistant", text: "" }]);
    setBusy(true);
    try {
      const response = await fetch(`${API}/api/assistant/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
        body: JSON.stringify({ symbol, question: prompt })
      });
      if (!response.ok || !response.body) {
        const detail = await response.text();
        throw new Error(detail || "Assistant request failed");
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let answer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";
        for (const block of events) {
          const eventName = block.match(/^event:\s*(.+)$/m)?.[1]?.trim();
          const dataLine = block.split("\n").find(line => line.startsWith("data:"));
          if (!dataLine) continue;
          let data;
          try { data = JSON.parse(dataLine.slice(5).trim()); } catch { continue; }
          if (eventName === "token") {
            answer += data.text || "";
            setMessages(old => {
              const next = [...old];
              next[next.length - 1] = { role: "assistant", text: answer };
              return next;
            });
          } else if (eventName === "error") {
            throw new Error(data.message || "Assistant stream failed");
          }
        }
      }
    } catch (e) {
      setError(e.message || "Could not reach the assistant. Check that the backend is running.");
      setMessages(old => old.map((m, i) => i === old.length - 1 && m.role === "assistant" && !m.text
        ? { ...m, text: "I couldn't complete that request." } : m));
    } finally {
      setBusy(false);
    }
  }

  return <article className="panel assistant">
    <div className="assistant-title"><BrainCircuit/><div><h2>Research assistant</h2><small>LangGraph · local model ready</small></div><span className="beta">AI</span></div>
    <div className="notice"><Sparkles size={14} style={{display:"inline",verticalAlign:"middle"}}/> Answers use a market-data snapshot. If Ollama is unavailable, the API returns a research snapshot and setup guidance.</div>
    <div className="chat-log" aria-live="polite">
      {messages.length === 0 ? <div className="chat-empty"><b>What would you like to research?</b><p>Ask about {symbol}'s valuation, recent price action, business, or risks.</p>
        <button onClick={() => ask(`Summarize the latest available market snapshot for ${symbol} and explain what it does and does not tell us.`)} disabled={busy}>Summarize {symbol}</button>
        <button onClick={() => ask(`What fundamental risks and metrics should I investigate for ${symbol}?`)} disabled={busy}>Key risks and metrics</button>
      </div> : messages.map((m, i) => <div key={i} className={`chat-message ${m.role}`}><small>{m.role === "user" ? "YOU" : "MARKET INSIGHT"}</small><div className="message-text">{m.text || (busy && i === messages.length - 1 ? "Thinking…" : "")}</div></div>)}
      {busy && <div className="stream-status"><LoaderCircle size={13} className="spin"/> Researching {symbol}…</div>}
    </div>
    {error && <p className="chat-error">{error}</p>}
    <form className="chat-form" onSubmit={e => { e.preventDefault(); ask(); }}>
      <input value={question} onChange={e => setQuestion(e.target.value)} placeholder={`Ask about ${symbol}…`} aria-label="Ask the market research assistant" disabled={busy}/>
      <button aria-label="Send question" disabled={busy || !question.trim()}><Send size={15}/></button>
    </form>
    <div className="disclaimer">Educational research only · Not personalized financial advice</div>
  </article>;
}

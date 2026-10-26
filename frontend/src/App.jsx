import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Search, TrendingUp, BrainCircuit } from "lucide-react";
import AIResearchAssistant from "./AIResearchAssistant.jsx";
const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const money = (v, c="USD") => v == null ? "—" : new Intl.NumberFormat("en-US",{style:"currency",currency:c,maximumFractionDigits:2}).format(v);
export default function App() {
  const [input,setInput]=useState("AAPL"), [symbol,setSymbol]=useState("AAPL"), [period,setPeriod]=useState("1mo");
  const [quote,setQuote]=useState(null), [history,setHistory]=useState([]), [overview,setOverview]=useState(null);
  const [loading,setLoading]=useState(true), [error,setError]=useState("");
  useEffect(()=>{let live=true; async function load(){setLoading(true);setError("");try{
    const paths=["quote",`history?period=${period}&interval=1d`,"overview"];
    const data=await Promise.all(paths.map(async p=>{const r=await fetch(`${API}/api/stock/${encodeURIComponent(symbol)}/${p}`);const d=await r.json();if(!r.ok)throw Error(d.detail||"Request failed");return d;}));
    if(live){setQuote(data[0]);setHistory(data[1].points||[]);setOverview(data[2]);}
  }catch(e){if(live){setError(e.message);setQuote(null);setHistory([]);setOverview(null);}}finally{if(live)setLoading(false);}}load();return()=>{live=false};},[symbol,period]);
  const positive=(quote?.change??0)>=0;
  return <div className="shell"><aside><div className="brand"><TrendingUp/> market<span>insight</span></div><p className="nav-active">▦ &nbsp; Overview</p><p>◷ &nbsp; Market explorer</p><p><BrainCircuit size={16}/> &nbsp; AI research</p><div className="side-bottom">Educational research only<br/><small>Market data by yfinance</small></div></aside>
  <main><header><span>Workspace / <b>Overview</b></span><span className="live">● Data on request</span></header>
  <section className="intro"><div><small>YOUR MARKET RESEARCH DESK</small><h1>Market overview</h1><p>Explore price action and company fundamentals in one place.</p></div>
  <form onSubmit={e=>{e.preventDefault();if(input.trim())setSymbol(input.trim().toUpperCase())}}><Search size={17}/><input value={input} onChange={e=>setInput(e.target.value)} placeholder="Ticker symbol"/><button>Analyze</button></form></section>
  {error&&<div className="error"><b>Couldn’t load {symbol}.</b> {error}. Make sure the backend is running.</div>}
  <section className="metrics"><article><label>Last available price</label><h2>{loading?"Loading…":money(quote?.price,quote?.currency)}</h2><strong className={positive?"up":"down"}>{quote?.change_percent==null?"Change unavailable":`${positive?"+":""}${quote.change_percent.toFixed(2)}%`}</strong><small>{quote?.name||symbol}</small></article>
  <article><label>Market capitalization</label><h2>{overview?.market_cap==null?"—":new Intl.NumberFormat("en-US",{notation:"compact"}).format(overview.market_cap)}</h2><small>Company valuation</small></article>
  <article><label>52-week high</label><h2>{money(overview?.fifty_two_week_high,quote?.currency)}</h2><small>Trailing range</small></article><article><label>52-week low</label><h2>{money(overview?.fifty_two_week_low,quote?.currency)}</h2><small>Trailing range</small></article></section>
  <section className="columns"><article className="panel chart"><div className="panel-head"><div><small>PRICE PERFORMANCE</small><h2>{symbol} price history</h2><p>{quote?.name||symbol} · historical close</p></div><div className="periods">{["1mo","3mo","6mo","1y","5y"].map(p=><button className={period===p?"selected":""} onClick={()=>setPeriod(p)} key={p}>{p}</button>)}</div></div>
  <h2 className="price">{money(quote?.price,quote?.currency)} <span className={positive?"up":"down"}>{quote?.change_percent==null?"":`${positive?"+":""}${quote.change_percent.toFixed(2)}%`}</span></h2>
  <div className="graph">{loading?"Loading price history…":history.length?<ResponsiveContainer width="100%" height="100%"><AreaChart data={history}><defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#858bff" stopOpacity=".3"/><stop offset="100%" stopColor="#858bff" stopOpacity="0"/></linearGradient></defs><CartesianGrid stroke="#293149" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="date" tickFormatter={v=>new Date(v).toLocaleDateString(undefined,{month:"short",day:"numeric"})} tick={{fill:"#8792ad",fontSize:10}} minTickGap={30}/><YAxis domain={["auto","auto"]} tick={{fill:"#8792ad",fontSize:10}}/><Tooltip contentStyle={{background:"#141b2e",border:"1px solid #303852"}}/><Area dataKey="close" stroke="#858bff" fill="url(#fill)" strokeWidth={2}/></AreaChart></ResponsiveContainer>: "No chart data available"}</div><footer>Historical prices from Yahoo Finance · Not guaranteed real-time</footer></article>
  <AIResearchAssistant symbol={symbol} /></section>
  <section className="panel company"><small>COMPANY PROFILE</small><h2>{overview?.name||symbol}</h2><p>{overview?.sector||"Sector unavailable"} {overview?.industry?`· ${overview.industry}`:""}</p><div className="fundamentals"><div><small>Trailing P/E</small><b>{overview?.trailing_pe?.toFixed(2)??"—"}</b></div><div><small>Dividend yield</small><b>{overview?.dividend_yield==null?"—":`${(overview.dividend_yield*100).toFixed(2)}%`}</b></div><div><small>52-week range</small><b>{money(overview?.fifty_two_week_low,quote?.currency)} – {money(overview?.fifty_two_week_high,quote?.currency)}</b></div></div><p className="summary">{overview?.summary||"Company description appears here when the provider returns it."}</p></section>
  <footer className="bottom">© {new Date().getFullYear()} Market Insight <span>Verify data before making financial decisions.</span></footer></main></div>;
}

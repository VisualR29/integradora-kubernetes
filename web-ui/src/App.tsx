import { useCallback, useState, useEffect } from "react";
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend, ReferenceLine
} from 'recharts';
import { TrendingUp, TrendingDown, Minus, RefreshCw, Search, Wallet, Plus, Trash2 } from 'lucide-react';

type PricePoint = { ts: string; close: number; };

type SignalRecord = {
  symbol: string;
  result: "BUY" | "SELL" | "HOLD" | string;
  reason: string;
  sma5: number | null;
  sma20: number | null;
  pct_change: number | null;
};

type Summary = {
  symbol: string;
  prices: { points: PricePoint[]; source: string };
  signal: SignalRecord;
};

export default function App() {
  const [symbol, setSymbol] = useState("AAPL");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<Summary | null>(null);
  
  // Portafolio guardado en el navegador (Local Storage)
  const [portfolio, setPortfolio] = useState<{sym: string, price: number}[]>(() => {
    const saved = localStorage.getItem("heimdall_portfolio");
    return saved ? JSON.parse(saved) : [];
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/v1/summary?symbol=${encodeURIComponent(symbol)}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const body = (await r.json()) as Summary;
      setData(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  const addToPortfolio = () => {
    if (!data) return;
    const updated = [...portfolio, { sym: data.symbol, price: data.prices.points[data.prices.points.length - 1].close }];
    setPortfolio(updated);
    localStorage.setItem("heimdall_portfolio", JSON.stringify(updated));
  };

  const removeFromPortfolio = (index: number) => {
    const updated = portfolio.filter((_, i) => i !== index);
    setPortfolio(updated);
    localStorage.setItem("heimdall_portfolio", JSON.stringify(updated));
  };

  const getSignalConfig = (result: string) => {
    switch (result) {
      case "BUY": return { color: "text-green-600", bg: "bg-green-50", border: "border-green-200", icon: <TrendingUp size={28}/> };
      case "SELL": return { color: "text-red-600", bg: "bg-red-50", border: "border-red-200", icon: <TrendingDown size={28}/> };
      default: return { color: "text-slate-600", bg: "bg-slate-50", border: "border-slate-200", icon: <Minus size={28}/> };
    }
  };

  const config = getSignalConfig(data?.signal.result ?? "");

  return (
    <main className="dashboard-container">
      {/* HEADER CON IDENTIDAD HEIMDALL */}
      <header className="header">
        <div className="brand">
          <div className="logo-icon">H</div>
          <div>
            <h1>Heimdall <span className="badge">v1.0</span></h1>
          </div>
        </div>
        
        <div className="search-bar">
          <div className="input-group">
            <Search size={18} className="icon" />
            <input 
              value={symbol} 
              onChange={(e) => setSymbol(e.target.value.toUpperCase())} 
              placeholder="Ticker (AAPL, BTC...)"
            />
          </div>
          <button className="btn-primary" disabled={loading} onClick={() => void load()}>
            {loading ? <RefreshCw className="spin" size={18} /> : "Analizar"}
          </button>
        </div>
      </header>

      {error && <div className="error-box">{error}</div>}

      {data && (
        <div className="heimdall-layout">
          {/* 1. GRÁFICA PRINCIPAL (FULL WIDTH) */}
          <section className="card full-chart">
            <div className="card-header">
              <div className="symbol-info">
                <img 
                  src={`https://logo.clearbit.com/${data.symbol.toLowerCase()}.com`} 
                  onError={(e) => (e.currentTarget.src = "https://via.placeholder.com/40?text=" + data.symbol)}
                  className="ticker-logo"
                  alt="logo"
                />
                <h3>{data.symbol} </h3>
              </div>
              <button className="btn-outline" onClick={addToPortfolio}>
                <Plus size={16} /> Añadir al Portafolio
              </button>
            </div>

            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={data.prices.points}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis 
                    dataKey="ts" 
                    tickFormatter={(str) => { try { return str.split('T')[1].substring(0, 5) } catch { return str } }} 
                    fontSize={11}
                  />
                  <YAxis domain={['auto', 'auto']} fontSize={11} />
                  <Tooltip contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}} />
                  <Area 
                    type="monotone" 
                    dataKey="close" 
                    stroke="#2563eb" 
                    strokeWidth={3} 
                    fillOpacity={1} 
                    fill="url(#colorPrice)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* 2. GRID INFERIOR (SEÑAL + STATS + PORTAFOLIO) */}
          <div className="bottom-grid">
            {/* SEÑAL ACTUAL */}
            <div className={`card signal-card-v2 ${config.bg} ${config.border}`}>
              <div className="signal-badge">Recomendación Actual</div>
              <div className="signal-main">
                {config.icon}
                <h2 className={config.color}>{data.signal.result}</h2>
              </div>
              <p className="reason-text">{data.signal.reason}</p>
            </div>

            {/* STATS TÉCNICOS */}
            <div className="card metrics-card">
              <div className="metric-row">
                <span>SMA 5</span>
                <strong>${data.signal.sma5?.toFixed(2)}</strong>
              </div>
              <div className="metric-row">
                <span>SMA 20</span>
                <strong>${data.signal.sma20?.toFixed(2)}</strong>
              </div>
              <div className="metric-row highlight">
                <span>Variación</span>
                <span className={Number(data.signal.pct_change) >= 0 ? 'text-green-600' : 'text-red-600'}>
                  {data.signal.pct_change}%
                </span>
              </div>
            </div>

            {/* MI PORTAFOLIO (LOCAL) */}
            <div className="card portfolio-card">
              <div className="card-header-sm">
                <Wallet size={18} />
                <h4>Mi Portafolio</h4>
              </div>
              <div className="portfolio-list">
                {portfolio.length === 0 && <p className="muted small">Tu wallet está vacía</p>}
                {portfolio.map((item, i) => (
                  <div key={i} className="portfolio-item">
                    <span>{item.sym}</span>
                    <div className="item-actions">
                      <strong>${item.price.toFixed(2)}</strong>
                      <Trash2 size={14} className="delete-icon" onClick={() => removeFromPortfolio(i)} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
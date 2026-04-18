import { useCallback, useState } from "react";

type PricePoint = {
  ts: string;
  close: number;
};

type SignalRecord = {
  symbol: string;
  created_at: string;
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
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  const recalc = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/v1/signals/recalculate?symbol=${encodeURIComponent(symbol)}`, {
        method: "POST",
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const s = await fetch(`/api/v1/summary?symbol=${encodeURIComponent(symbol)}`);
      if (!s.ok) throw new Error(`HTTP ${s.status}`);
      setData((await s.json()) as Summary);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  const pillClass =
    data?.signal.result === "BUY"
      ? "buy"
      : data?.signal.result === "SELL"
        ? "sell"
        : "hold";

  const tail = data?.prices.points.slice(-8) ?? [];

  return (
    <main>
      <h1>Señales de inversión (simulado)</h1>
      <p className="muted">Datos mock y reglas simples. Sin operaciones reales.</p>
      <div className="row">
        <label htmlFor="sym">Símbolo</label>
        <input id="sym" value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
        <button type="button" className="primary" disabled={loading} onClick={() => void load()}>
          {loading ? "Cargando…" : "Resumen"}
        </button>
        <button type="button" className="secondary" disabled={loading} onClick={() => void recalc()}>
          Recalcular señal
        </button>
      </div>
      {error ? <p className="error">{error}</p> : null}
      {data ? (
        <>
          <p>
            Fuente precios: <strong>{data.prices.source}</strong> · Última señal:{" "}
            <span className={`pill ${pillClass}`}>{data.signal.result}</span>
          </p>
          <p className="muted">
            Motivo: {data.signal.reason} · SMA5: {data.signal.sma5?.toFixed(4) ?? "—"} · SMA20:{" "}
            {data.signal.sma20?.toFixed(4) ?? "—"} · Δ% ventana:{" "}
            {data.signal.pct_change != null ? `${data.signal.pct_change}%` : "—"}
          </p>
          <h2 style={{ fontSize: "1rem", marginTop: "1.25rem" }}>Últimos cierres</h2>
          <table>
            <thead>
              <tr>
                <th>Hora (UTC)</th>
                <th>Cierre</th>
              </tr>
            </thead>
            <tbody>
              {tail.map((p) => (
                <tr key={p.ts}>
                  <td>{p.ts}</td>
                  <td>{p.close}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : null}
    </main>
  );
}

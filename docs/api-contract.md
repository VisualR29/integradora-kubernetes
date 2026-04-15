# Contrato API v0.1

Intercambio **JSON** con `Content-Type: application/json`. Tiempos en **ISO 8601** (UTC).

## Modelos compartidos

### PricePoint

| Campo       | Tipo   | Descripción                          |
|------------|--------|--------------------------------------|
| `ts`       | string | Marca de tiempo ISO 8601             |
| `open`     | number | Apertura (mock puede igualar close)|
| `high`     | number | Máximo                               |
| `low`      | number | Mínimo                               |
| `close`    | number | Cierre                               |
| `volume`   | number | Volumen simulado                     |

### PriceSeriesResponse

| Campo      | Tipo            | Descripción        |
|-----------|-----------------|--------------------|
| `symbol`  | string          | Ticker normalizado |
| `source`  | string          | `mock` \| `public` |
| `points`  | array PricePoint| Orden cronológico  |

### SignalResult

Valor de `result`: `BUY` | `SELL` | `HOLD`.

### SignalRecord

| Campo        | Tipo   | Descripción                    |
|-------------|--------|--------------------------------|
| `symbol`    | string | Ticker                         |
| `created_at`| string | ISO 8601                       |
| `result`    | string | BUY / SELL / HOLD              |
| `reason`    | string | Texto breve de la regla        |
| `sma5`      | number \| null | Última SMA(5)           |
| `sma20`     | number \| null | Última SMA(20)          |
| `pct_change`| number \| null | Cambio % en la ventana  |

## market-data

### `GET /health`

200: `{"status":"ok"}`

### `GET /metrics`

Texto formato Prometheus.

### `GET /prices/{symbol}`

Query: `limit` (opcional, default 60, max 500).

**200:** `PriceSeriesResponse`

**404:** símbolo vacío o inválido.

## signal-engine

### `GET /health`

200: `{"status":"ok"}`

### `GET /metrics`

Texto formato Prometheus.

### `GET /signals/latest`

Query: `symbol` (requerido).

**200:** último `SignalRecord` persistido o generado en caliente si no hay historial.

### `POST /signals/generate`

Query: `symbol` (requerido). Obtiene precios de market-data, calcula señal, persiste.

**200:** `SignalRecord`

### `GET /signals/history`

Query: `symbol`, `limit` (default 20, max 100).

**200:** `{ "items": [ SignalRecord, ... ] }`

## api-bff

### `GET /api/v1/summary`

Query: `symbol` (requerido). **200:** `{ "symbol", "prices": PriceSeriesResponse, "signal": SignalRecord }`

### `POST /api/v1/signals/recalculate`

Query: `symbol`. Proxies a signal-engine `POST /signals/generate`. **200:** `SignalRecord`

### `GET /health`

Comprobación del BFF.

### `GET /metrics`

Texto formato Prometheus.

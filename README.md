# Integradora: señales de inversión (microservicios)

MVP académico: datos de mercado desde **Tiingo** y/o **Twelve Data** (si configuras claves), con **cache en PostgreSQL** y **respaldo mock** si no hay claves o falla la API. Reglas simples (SMA y cambio %), señales **BUY / SELL / HOLD**. **No** hay ejecución de órdenes ni dinero real.

**Guía paso a paso (local, dev, K8s, imágenes):** [docs/GUIA.md](docs/GUIA.md)

## Requisitos

- Docker y Docker Compose
- (Opcional) Python 3.12 y Node 20 para desarrollo local

## Arranque local

Copiá la plantilla de variables (opcional, para APIs reales):

```bash
cp .env.example .env
# Editá .env y pegá MARKET_TIINGO_TOKEN y/o MARKET_TWELVEDATA_API_KEY
```

Docker Compose lee automáticamente un archivo **`.env`** en la raíz del proyecto para sustituir variables en `docker-compose.yml`. Ese archivo **no** está en el repo (está ignorado en `.gitignore`).

```bash
docker compose up --build
```

Variables opcionales para **market-data** (definilas en `.env` o en el entorno antes de `docker compose`):

| Variable | Descripción |
|----------|-------------|
| `MARKET_TIINGO_TOKEN` | Token de [Tiingo](https://www.tiingo.com/account/api/token) |
| `MARKET_TWELVEDATA_API_KEY` | Clave de [Twelve Data](https://twelvedata.com/) |
| `MARKET_PROVIDER_ORDER` | Orden de intento, por defecto `tiingo,twelvedata,mock` |
| `MARKET_STALE_AFTER_SECONDS` | Segundos desde la **última sincronización exitosa** con Tiingo/Twelve Data (tabla `market.price_sync_meta`) tras la cual se sirve Postgres sin volver a llamar a la API (por defecto 86400). **No** usa la fecha de la última vela EOD (eso hacía que casi siempre se reconsultara la API). |
| `MARKET_ALLOWED_SYMBOLS` | Lista separada por comas (ej. `AAPL,MSFT`). Si está definida y no vacía, cualquier otro símbolo responde **403** (modo demo / ahorro de cuota) |
| `MARKET_CACHE_SERVE_MIN_ROWS` | Mínimo de velas en Postgres para servir cache si `last_sync` es fresco pero hay menos filas que `limit` (por defecto **26**, alineado a SMA20 + margen). Evita otra API cuando el BFF y el motor pedían límites distintos. |

El **api-bff** pide a `market-data` **60** velas en el resumen (`summary_prices_limit` en `services/api-bff/app/config.py`, alineado al `need` del `signal-engine`), para que un solo “Analizar” no dispare dos consumos de API externa (antes: 40 en el BFF y 60 en el motor).

Los datos OHLC diarios en cache viven en el esquema `market.price_candles` del mismo Postgres que usa `signal-engine`. El volumen `postgres_data` en Compose hace que sobreviva a `docker compose down` (sin `-v`).

### Modo demo (símbolos fijos + frescura del cache)

- **Limitar tickers:** en `.env` definí `MARKET_ALLOWED_SYMBOLS=AAPL,MSFT` (o los que uses en la exposición). Así la UI y los compañeros no pueden disparar consultas a símbolos arbitrarios y consumir la API gratuita.
- **Frescura:** `MARKET_STALE_AFTER_SECONDS` mide el tiempo desde la **última vez** que `market-data` guardó datos tras una respuesta OK de Tiingo/Twelve Data, no la antigüedad del último precio diario. Así, si pulsás “Analizar” varias veces en segundos, la segunda debería servirse desde Postgres (`source: postgres`) sin nueva llamada a la API externa (mientras no venza ese TTL).

### URLs locales

- **market-data:** http://localhost:8001/docs  
- **signal-engine:** http://localhost:8002/docs  

Ejemplos:

```bash
curl "http://localhost:8001/prices/AAPL?limit=30"
curl "http://localhost:8002/signals/latest?symbol=AAPL"
curl -X POST "http://localhost:8002/signals/generate?symbol=AAPL"
```

Con el stack completo (BFF + UI): **http://localhost:3000** — ver [docs/runbook.md](docs/runbook.md).

## Estructura

- `services/market-data` — precios (Tiingo / Twelve Data), cache Postgres, mock de respaldo  
- `services/signal-engine` — motor de señales y PostgreSQL  
- `services/api-bff` — agregación para el frontend  
- `web-ui` — SPA React  
- `charts/signals-platform` — Helm umbrella  
- `.github/workflows` — CI/CD  

## Ramas

Se recomienda `main` (estable) y `dev` (integración), con PRs revisados.

## Licencia

MIT — ver [LICENSE](LICENSE).

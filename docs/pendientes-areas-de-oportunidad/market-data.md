# market-data

## Orden sugerido de desarrollo (proyecto)

1. **GitHub** — CI en cada cambio; release e imágenes cuando el código compile y pase pruebas.
2. **market-data** — Fuente de precios estable (mock primero; proveedor real después).
3. **signal-engine** — Reglas y persistencia; depende de market-data y Postgres.
4. **api-bff** — Agregación para la UI; depende de market-data y signal-engine.
5. **web-ui** — Pantalla sobre el contrato del BFF.
6. **charts** — Empaquetado Helm (imágenes, Postgres, Ingress, probes).
7. **deploy** — Compose local, namespaces y procedimiento de instalación/upgrade.
8. **monitoring** — Scrape, dashboards y alertas sobre un despliegue ya funcional.

**Este documento:** paso **2** de 8 — es la base de datos “de mercado” para signal-engine y el resumen del BFF.

## Cómo funciona actualmente

- **Stack**: FastAPI; modelos Pydantic para puntos OHLCV y respuesta de serie (`source` documentado en OpenAPI).
- **Endpoint principal**: `GET /prices/{symbol}?limit=` — valida símbolo, acota `limit` entre mínimo/máximo (`MARKET_*`).
- **Fuentes**: orden configurable `MARKET_PROVIDER_ORDER` (por defecto `tiingo,twelvedata,mock`). **Tiingo** y **Twelve Data** vía `httpx.AsyncClient`; **PostgreSQL** como cache (`MARKET_DATABASE_URL`) con frescura según `MARKET_STALE_AFTER_SECONDS` y `MARKET_CACHE_SERVE_MIN_ROWS`; **mock** determinista en `mock_series.py` si no hay datos externos ni cache útil.
- **Respuesta**: `source` puede ser `tiingo`, `twelvedata`, `postgres`, `postgres_stale` o `mock`.
- **Seguridad demo**: `MARKET_ALLOWED_SYMBOLS` opcional — símbolos fuera de la lista → **403**.
- **Símbolo inválido**: **400** (alineado con BFF/signal-engine).
- **Observabilidad**: `/health`, `/metrics`; contador `FETCH` por fuente y estado; histograma `market_data_provider_request_seconds` para llamadas salientes a Tiingo/Twelve Data.

## Áreas de mejora

- **Límites de tasa** por proveedor (backoff, colas) si el tráfico crece.
- **Granularidad** distinta de velas diarias (requiere acordar contrato con consumidores).
- **Dashboards** que exploten `FETCH`, `PROVIDER_LATENCY` y latencia HTTP del propio servicio.

## Trabajo que falta

- Afinar políticas de cuota/coste por entorno (demo vs producción).
- Opcional: alertas Prometheus sobre ratio de `FETCH` con estado distinto de `ok` por proveedor.

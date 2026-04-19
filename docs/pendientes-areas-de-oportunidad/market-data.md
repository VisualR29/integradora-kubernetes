# market-data

## Cómo funciona actualmente

- **Stack**: FastAPI; modelos Pydantic para puntos OHLCV y respuesta de serie.
- **Endpoint principal**: `GET /prices/{symbol}?limit=` — valida símbolo (alfanumérico con puntos), acota `limit` entre configuración mínima/máxima (`MARKET_DEFAULT_PRICE_LIMIT`, `MARKET_MAX_PRICE_LIMIT`, etc. vía prefijo `MARKET_`).
- **Fuente de datos**: **no hay proveedor externo**. La serie se genera en memoria en `mock_series.py`: semilla determinista a partir del hash del símbolo, ondas seno/coseno y ruido; timestamps en UTC desde “ahora” del servidor.
- **Respuesta**: incluye `source: "mock"` y la lista de `PricePoint`.
- **Observabilidad**: `/health`, `/metrics` (Prometheus), contador `FETCH` etiquetado como fuente `mock` y estado `ok`.

## Áreas de mejora

- Sustituir o complementar el mock con **datos reales** (API de mercado, claves, límites de tasa).
- **Semántica HTTP**: símbolo inválido devuelve `404`; muchas APIs usan `400`.
- **Caché y coste**: recalcular serie en cada request; con datos reales hará falta caché por símbolo/ventana.
- **Concurrencia**: handler síncrono; aceptable para mock, insuficiente si se añade I/O bloqueante sin `async`.
- **Observabilidad**: métricas de error/latencia hacia proveedor externo cuando exista.

## Trabajo que falta

- Definir proveedor, modelo de autenticación y almacenamiento de secretos.
- Implementar cliente HTTP async, manejo de errores y métricas `FETCH` con estados reales.
- Ajustar contrato (`source`, granularidad, timezone) con consumidores (`signal-engine`, `api-bff`, documentación).
- Ampliar tests (límites, determinismo, fallos simulados del proveedor).

# signal-engine

## Orden sugerido de desarrollo (proyecto)

1. **GitHub** — CI en cada cambio; release e imágenes cuando el código compile y pase pruebas.
2. **market-data** — Fuente de precios estable (mock primero; proveedor real después).
3. **signal-engine** — Reglas y persistencia; depende de market-data y Postgres.
4. **api-bff** — Agregación para la UI; depende de market-data y signal-engine.
5. **web-ui** — Pantalla sobre el contrato del BFF.
6. **charts** — Empaquetado Helm (imágenes, Postgres, Ingress, probes).
7. **deploy** — Compose local, namespaces y procedimiento de instalación/upgrade.
8. **monitoring** — Scrape, dashboards y alertas sobre un despliegue ya funcional.

**Este documento:** paso **3** de 8 — requiere market-data (y Postgres) para probar de punta a punta.

## Cómo funciona actualmente

- **Stack**: FastAPI, SQLAlchemy async + `asyncpg`, `httpx` para llamar a **market-data**.
- **Arranque**: crea motor BD, ejecuta `init_schema` (esquema `signals`, tabla `signal_history`, índice), abre `httpx.AsyncClient`.
- **Lógica** (`logic.py`): reglas fijas sobre cierres — SMA corta/larga (por defecto 5 y 20), cruce alcista/bajista, y momentum por cambio porcentual en una ventana (por defecto 24 puntos) frente a umbrales configurables. Resultado `BUY`, `SELL` u `HOLD` con texto de `reason`.
- **Endpoints**:
  - `POST /signals/generate`: obtiene precios vía `fetch_prices` → calcula señal → **inserta** en BD → devuelve registro.
  - `GET /signals/latest`: si hay fila reciente en BD para el símbolo, la devuelve; si no, calcula como arriba, inserta y devuelve.
  - `GET /signals/history`: lista histórica acotada (máx. 100).
- **Configuración**: `MARKET_DATA_BASE_URL`, `DATABASE_URL`, umbrales SMA y porcentuales por variables de entorno (clase `Settings` sin prefijo único de servicio).
- **Observabilidad**: métricas HTTP propias, `MARKET_FETCH` (ok/error) y `SIGNAL_GEN` por resultado/motivo.

## Áreas de mejora

- **Datos de entrada**: depende de series **mock** de market-data; la señal no refleja mercados reales hasta que market-data evolucione.
- **Política de “latest”**: mezcla “último persistido” con generación bajo demanda sin TTL claro ni versionado de reglas.
- **Migraciones**: el esquema se crea con SQL embebido al arranque; no hay herramienta tipo Alembic ni migraciones versionadas.
- **Transacciones y concurrencia**: posibles condiciones de carrera si varias instancias generan señales al mismo tiempo (sin bloqueo por símbolo).
- **Modelo de dominio**: reglas simples de demo; falta backtesting, configuración por símbolo, o capa de estrategias plug-in.

## Trabajo que falta

- Alinear umbrales y ventanas con producto y documentar en runbook/contrato API.
- Introducir migraciones de BD y política de retención/archivado de `signal_history`.
- Definir comportamiento cuando market-data falla o devuelve datos insuficientes (hoy `502` con `market_data_unavailable`).
- Tests de integración con BD de prueba y cliente HTTP mockeado.
- Opcional: jobs programados para precalcular señales en lugar de solo bajo demanda.

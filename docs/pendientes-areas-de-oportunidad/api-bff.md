# api-bff (Backend for Frontend)

## Orden sugerido de desarrollo (proyecto)

1. **GitHub** — CI en cada cambio; release e imágenes cuando el código compile y pase pruebas.
2. **market-data** — Fuente de precios estable (mock primero; proveedor real después).
3. **signal-engine** — Reglas y persistencia; depende de market-data y Postgres.
4. **api-bff** — Agregación para la UI; depende de market-data y signal-engine.
5. **web-ui** — Pantalla sobre el contrato del BFF.
6. **charts** — Empaquetado Helm (imágenes, Postgres, Ingress, probes).
7. **deploy** — Compose local, namespaces y procedimiento de instalación/upgrade.
8. **monitoring** — Scrape, dashboards y alertas sobre un despliegue ya funcional.

**Este documento:** paso **4** de 8 — conviene tener market-data y signal-engine razonablemente cerrados antes de endurecer el BFF y su contrato.

> En el repositorio el servicio se llama **`api-bff`**. Si te referías a “api.biff”, es el mismo componente: capa BFF frente al navegador.

## Cómo funciona actualmente

- **Stack**: FastAPI, `httpx.AsyncClient` creado en el `lifespan` con timeout configurable.
- **CORS**: abierto (`allow_origins=["*"]`) para facilitar desarrollo y demos.
- **Observabilidad**: middleware que registra contador e histograma de latencia por método/ruta (excepto `/metrics`); `GET /metrics` en Prometheus; `APP_INFO` al arrancar.
- **Rutas principales**:
  - `GET /health`: estado simple.
  - `GET /api/v1/summary?symbol=`: en paralelo llama a **market-data** (`/prices/{symbol}` con `limit=40`) y a **signal-engine** (`/signals/latest?symbol=`), y devuelve un agregado (`SummaryResponse`).
  - `POST /api/v1/signals/recalculate?symbol=`: delega en **signal-engine** (`POST /signals/generate`) y devuelve el `SignalRecord`.
- **Configuración** (`app/config.py`): URLs base por defecto `http://market-data:8000` y `http://signal-engine:8000`, timeout de petición ~15 s. Sin prefijo de entorno explícito en el modelo (variables en mayúsculas estándar de Pydantic Settings).

## Áreas de mejora

- **Seguridad**: CORS permisivo; sin autenticación, rate limiting ni validación de origen en producción.
- **Resiliencia**: errores aguas abajo se traducen en `502` genéricos (`market_data_error`, `signal_engine_error`); sin reintentos selectivos, circuit breaker ni degradación parcial (p. ej. precios sin señal).
- **Contrato API**: el BFF fija `limit=40` en precios sin exponerlo al cliente; podría desalinearse con lo que necesita la UI o el contrato documentado.
- **Configuración**: falta homogeneizar prefijos `MARKET_` / documentación de variables respecto a otros servicios.
- **Observabilidad**: no hay métricas específicas de llamadas salientes por dependencia (solo latencia HTTP del BFF).

## Trabajo que falta

- Endurecer CORS y/o API gateway delante del BFF.
- Mapear códigos y cuerpos de error más ricos (sin filtrar secretos).
- Opcional: exponer `limit` o parámetros de resumen alineados con `docs/api-contract.md`.
- Pruebas de integración con dependencias mockeadas (hoy hay tests mínimos de salud).
- Timeouts y políticas de reintento alineadas con SLO del cluster.

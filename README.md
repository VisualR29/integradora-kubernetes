# Integradora: señales de inversión (microservicios)

MVP académico: datos de mercado **simulados**, reglas simples (SMA y cambio %), señales **BUY / SELL / HOLD**. **No** hay ejecución de órdenes ni dinero real.

**Guía paso a paso (local, dev, K8s, imágenes):** [docs/GUIA.md](docs/GUIA.md)

## Requisitos

- Docker y Docker Compose
- (Opcional) Python 3.12 y Node 20 para desarrollo local

## Arranque local

```bash
docker compose up --build
```

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

- `services/market-data` — serie de precios mock  
- `services/signal-engine` — motor de señales y PostgreSQL  
- `services/api-bff` — agregación para el frontend  
- `web-ui` — SPA React  
- `charts/signals-platform` — Helm umbrella  
- `.github/workflows` — CI/CD  

## Ramas

Se recomienda `main` (estable) y `dev` (integración), con PRs revisados.

## Licencia

MIT — ver [LICENSE](LICENSE).

# web-ui

## Orden sugerido de desarrollo (proyecto)

1. **GitHub** — CI en cada cambio; release e imágenes cuando el código compile y pase pruebas.
2. **market-data** — Fuente de precios estable (mock primero; proveedor real después).
3. **signal-engine** — Reglas y persistencia; depende de market-data y Postgres.
4. **api-bff** — Agregación para la UI; depende de market-data y signal-engine.
5. **web-ui** — Pantalla sobre el contrato del BFF.
6. **charts** — Empaquetado Helm (imágenes, Postgres, Ingress, probes).
7. **deploy** — Compose local, namespaces y procedimiento de instalación/upgrade.
8. **monitoring** — Scrape, dashboards y alertas sobre un despliegue ya funcional.

**Este documento:** paso **5** de 8 — desarrollar cuando el BFF exponga de forma estable `summary` y `recalculate`.

## Cómo funciona actualmente

- **Stack**: React + Vite + TypeScript; estilos en `styles.css`.
- **Flujo de usuario**: un único pantallazo — título, aviso de datos simulados, input de símbolo, botones “Resumen” y “Recalcular señal”.
- **Llamadas HTTP**:
  - `GET /api/v1/summary?symbol=` para cargar precios (vía BFF) y última señal.
  - `POST /api/v1/signals/recalculate?symbol=` y luego otro `GET .../summary` para refrescar tras recalcular.
- **Desarrollo local**: `vite.config.ts` hace **proxy** de `/api` hacia `http://localhost:8080` (api-bff).
- **Producción (contenedor)**: **nginx** sirve el estático y proxifica `/api/` a `http://api-bff:8000/api/` (`nginx.conf`).

## Áreas de mejora

- **Experiencia**: sin rutas, sin historial de señales en UI (aunque el backend expone `/signals/history`), sin gráficos, accesibilidad y i18n mínimas.
- **Robustez**: errores solo como texto genérico (`HTTP 4xx/5xx`); sin reintentos ni estados vacíos guiados.
- **Configuración**: base URL de API implícita (mismo origen + proxy); no hay env/build-time para entornos múltiples sin tocar nginx/vite.
- **Calidad frontend**: sin tests E2E ni unitarios visibles en el repo; CI solo hace `npm run build`.
- **Seguridad**: asume que el BFF y el proxy son de confianza; no hay autenticación de usuario.

## Trabajo que falta

- Consumir endpoints adicionales (historial, metadatos) si el producto lo requiere.
- Mejorar manejo de errores, loading states y validación de símbolo en cliente.
- Añadir pruebas (Vitest/RTL, Playwright) según prioridad.
- Documentar despliegue detrás de Ingress (solo `/` al web-ui; las APIs van por el mismo host gracias al proxy nginx).

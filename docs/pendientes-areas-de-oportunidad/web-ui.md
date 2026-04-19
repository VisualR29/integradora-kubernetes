# web-ui

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

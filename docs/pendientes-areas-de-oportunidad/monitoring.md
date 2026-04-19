# monitoring

## Cómo funciona actualmente

- **Métricas de aplicación**: los tres backend (`market-data`, `signal-engine`, `api-bff`) exponen `GET /metrics` en formato Prometheus (contadores, histogramas, info según servicio).
- **Descubrimiento en Kubernetes**: los `Service` generados por el chart llevan anotaciones `prometheus.io/scrape`, `port`, `path` para configuraciones tipo `kubernetes_sd_configs` (endpoints), como describe `monitoring/README.md`.
- **Prometheus Operator**: el chart puede crear un `ServiceMonitor` si `prometheus.serviceMonitor.enabled: true` en `values.yaml`; **por defecto está en `false`**, así que no se crea el recurso sin acción explícita.
- **Grafana**: hay un dashboard exportado en JSON (`monitoring/grafana/dashboards/signals-overview.json`) pensado para importación manual y datasource Prometheus del cluster.
- **Reglas de alerta**: carpeta `monitoring/prometheus-rules/` con `.gitkeep` — sin reglas versionadas aún.
- **Evidencias**: se sugiere documentación en `docs/evidence/` para capturas de targets y paneles.

## Áreas de mejora

- **Activación end-to-end**: ServiceMonitor desactivado; sin kube-prometheus-stack u operador, las métricas pueden no scrapearse en absoluto.
- **Alerting**: ausencia de `PrometheusRule` para SLO básicos (errores 5xx, latencia, caída de dependencias).
- **Trazas**: no hay OpenTelemetry/Jaeger en los servicios.
- **Logs**: sin convención de logs estructurados ni agregación (Loki, ELK) descrita en código.
- **Dashboard**: puede quedar desalineado con métricas reales si cambian nombres o labels.

## Trabajo que falta

- Habilitar y validar `ServiceMonitor` en un cluster con Prometheus Operator, o documentar scrape config alternativa.
- Añadir reglas de alerta mínimas y revisar el dashboard contra métricas vigentes (`signals_*` namespaces/subsystems).
- Definir retención y acceso (quién ve Grafana, datasource gestionado).
- Completar carpeta de evidencias con capturas requeridas por la rúbrica o el runbook.

# Monitoreo

## Métricas de aplicación

Los servicios `market-data`, `signal-engine` y `api-bff` exponen `GET /metrics` en formato Prometheus.

En Kubernetes, los `Service` del chart incluyen anotaciones `prometheus.io/*` para descubrimiento típico con `kubernetes_sd_configs` (role: endpoints) o equivalente en kube-prometheus-stack.

## ServiceMonitor (Prometheus Operator)

En `charts/signals-platform/values.yaml`:

```yaml
prometheus:
  serviceMonitor:
    enabled: true
```

Requiere el CRD `ServiceMonitor` instalado (por ejemplo kube-prometheus-stack).

## Grafana

Importar el dashboard JSON:

- Archivo: [grafana/dashboards/signals-overview.json](grafana/dashboards/signals-overview.json)
- Grafana → Dashboards → Import → pegar JSON o subir archivo.
- Seleccionar datasource Prometheus del cluster.

## Evidencias

Guardar capturas de **Targets UP**, paneles del dashboard y consultas PromQL en `docs/evidence/`.

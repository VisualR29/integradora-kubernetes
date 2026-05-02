# charts (Helm — `signals-platform`)

## Orden sugerido de desarrollo (proyecto)

1. **GitHub** — CI en cada cambio; release e imágenes cuando el código compile y pase pruebas.
2. **market-data** — Fuente de precios estable (mock primero; proveedor real después).
3. **signal-engine** — Reglas y persistencia; depende de market-data y Postgres.
4. **api-bff** — Agregación para la UI; depende de market-data y signal-engine.
5. **web-ui** — Pantalla sobre el contrato del BFF.
6. **charts** — Empaquetado Helm (imágenes, Postgres, Ingress, probes).
7. **deploy** — Compose local, namespaces y procedimiento de instalación/upgrade.
8. **monitoring** — Scrape, dashboards y alertas sobre un despliegue ya funcional.

**Este documento:** paso **6** de 8 — ajustar el chart cuando las imágenes y variables de los servicios estén definidas.

## Cómo funciona actualmente

- **Chart principal**: `charts/signals-platform`, versión de chart/app `0.1.0`.
- **Dependencia**: subchart **Bitnami PostgreSQL** (`postgresql.enabled`), credenciales y tamaño de PVC configurables en `values.yaml`.
- **Plantillas**: Deployments + Services para `market-data`, `signal-engine`, `api-bff`, `web-ui`; variables de entorno que cablean URLs internas (`http://<release>-market-data:8000`, etc.); **Secret** para `DATABASE_URL` del signal-engine; **Ingress** opcional hacia el **Service** del web-ui (puerto 80); **ConfigMap** con nginx del web-ui; **ServiceMonitor** condicionado por `prometheus.serviceMonitor.enabled` (por defecto **false**).
- **Servicios**: anotaciones `prometheus.io/scrape` en los Service para descubrimiento clásico.
- **Imágenes**: valores por defecto `ghcr.io/example/signals-*:dev` — placeholders hasta configurar registry real.

## Áreas de mejora

- **Seguridad**: contraseña de Postgres por defecto en values (adecuado solo para demo); falta integración con Sealed Secrets / External Secrets / SOPS.
- **Alta disponibilidad**: réplicas 1 para todo; sin PDB, sin topology spread, sin HPA.
- **Networking**: el Ingress solo enruta al front; es coherente con el proxy `/api` en nginx, pero debe documentarse para quien espere Ingress al BFF directamente.
- **Observabilidad**: ServiceMonitor deshabilitado por defecto; reglas Prometheus en `monitoring/prometheus-rules/` pueden estar vacías (`.gitkeep`).
- **Operación**: sin hooks de migración explícitos; el signal-engine crea esquema al arrancar.

## Trabajo que falta

- Sustituir imágenes y `imagePullSecrets` por los valores del equipo tras el primer push a GHCR.
- Valores por entorno (`values-dev.yaml`, `values-prod.yaml`) y documentación de instalación (`helm install` con namespace).
- Endurecer secretos, recursos y probes según observación en cluster.
- Evaluar `NetworkPolicy`, límites de seguridad de contenedor y actualización del subchart de PostgreSQL.

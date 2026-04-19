# deploy (entornos y despliegue local)

## Cómo funciona actualmente

- **`docker-compose.yml`**: orquesta **Postgres 16**, **market-data** (8001→8000), **signal-engine** (8002→8000) con `DATABASE_URL` y `MARKET_DATA_BASE_URL`, **api-bff** (8080→8000) con URLs a los otros servicios, **web-ui** (3000→80) que depende del BFF. Healthcheck en Postgres; `depends_on` básico entre servicios.
- **`deploy/namespaces.yaml`**: define el namespace `signals-dev` con etiqueta `part-of: signals-platform` — recurso mínimo para organización en Kubernetes (no despliega workloads por sí solo).
- **Kubernetes “real”**: el camino previsto es **Helm** (`charts/signals-platform`); el release workflow genera el paquete `.tgz`. La guía operativa adicional está en `docs/runbook.md` (referencia cruzada).

## Áreas de mejora

- **Brecha compose vs K8s**: en compose no hay Ingress ni TLS; en K8s el acceso externo pasa por Ingress al front — comportamientos distintos para el mismo código.
- **Paridad de configuración**: credenciales y hosts difieren entre compose (`signals`/`signals`) y values del chart (`signals-dev-password`, host `signals.local.test`).
- **Automatización**: no hay script/Make target unificado “levantar todo” / “instalar chart” en el repo (salvo documentación).
- **Producción**: falta checklist de backup de Postgres, upgrades y rollback documentados en un solo lugar.

## Trabajo que falta

- Documentar flujo completo: desde `docker compose up` hasta `helm upgrade --install` con valores del equipo.
- Opcional: añadir perfiles compose (perfil mínimo sin web, etc.) o alinear puertos con la guía de clase.
- Definir estrategia de secretos y namespaces (`signals-dev` vs otros) para entregas evaluables.
- Integrar referencias a evidencias (`docs/evidence/`) tras cada despliegue de prueba.

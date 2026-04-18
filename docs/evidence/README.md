# Evidencias para entrega

Colocar aquí artefactos para la rúbrica (capturas, exports, enlaces internos del curso).

## Checklist sugerido

- [ ] Diagrama de arquitectura (export desde `docs/architecture.md` o herramienta C4) — PNG/PDF.
- [ ] Azure Portal: recurso **AKS** visible.
- [ ] `kubectl get pods,svc,ingress -n signals-dev` (o el namespace usado).
- [ ] `helm list -n signals-dev` y `helm history` tras un upgrade.
- [ ] GitHub Actions: captura de pipeline **CI** en verde.
- [ ] GitHub Release con artefacto `.tgz` del chart (workflow `release.yml`).
- [ ] Prometheus: targets **UP** para servicios con `/metrics`.
- [ ] Grafana: dashboard importado desde `monitoring/grafana/dashboards/signals-overview.json`.
- [ ] Swagger/OpenAPI accesible (`/docs` en BFF o servicios).
- [ ] Vídeo demo corto (5–8 min): UI → señal → métricas — subir donde indique el curso y enlazar aquí.

## Vídeo demo

- **Enlace:** _(completar tras grabación)_
- **Fecha:** _(YYYY-MM-DD)_

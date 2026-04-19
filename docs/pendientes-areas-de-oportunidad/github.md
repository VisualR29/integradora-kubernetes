# GitHub (repositorio y automatización)

## Cómo funciona actualmente

- **CI** (`.github/workflows/ci.yml`): en `push`/`pull_request` a `main`, `dev`, `develop`.
  - Job **python-services** en matriz: `market-data`, `signal-engine`, `api-bff` — instala dependencias, **ruff check**, **pytest**, build Docker **sin push** hacia GHCR con tag `ci-<sha>`.
  - Job **web-ui**: `npm install`, `npm run build`, build Docker sin push.
- **Release** (`.github/workflows/release.yml`): al etiquetar `v*.*.*`:
  - Build y **push** de imágenes de los tres servicios Python y de `web-ui` a `ghcr.io/<owner>/signals-*` con tag de versión y `latest`.
  - Job **helm-package**: `helm dependency update`, `helm package`, sube `.tgz` como artifact y adjunta al **GitHub Release** (`softprops/action-gh-release`).
- **Plantillas**: existe `pull_request_template.md` para estandarizar PRs.

## Áreas de mejora

- **Seguridad de cadena de suministro**: no hay escaneo de imágenes, SBOM ni firma de artefactos de forma visible.
- **Cobertura CI**: no hay job dedicado al chart (lint `helm lint`, kubeconform) ni despliegue automático a un cluster de prueba.
- **Versionado**: las imágenes del chart en `values.yaml` siguen siendo placeholders `ghcr.io/example/...` hasta que cada equipo los sustituya manualmente.
- **Ramas**: el flujo asume `dev`/`develop`; conviene documentar la estrategia de ramas y protecciones de `main`.

## Trabajo que falta

- Sincronizar documentación de release (quién crea tags, convención semver) con la guía del proyecto.
- Añadir comprobaciones Helm/Kubernetes en CI si el chart es parte crítica del entregable.
- Opcional: publicar chart en OCI/registry de charts, no solo adjunto al Release.
- Políticas de repositorio (branch protection, required checks) fuera del YAML pero deben alinearse con la asignatura/equipo.

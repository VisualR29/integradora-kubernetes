# Guía: cómo hacer funcionar el proyecto

Esta guía cubre el flujo **local con Docker** (recomendado para empezar), desarrollo opcional sin contenedores, despliegue en **Kubernetes (Helm)** y publicación de imágenes con **GitHub Actions**. No edita el plan del curso; solo describe el repositorio tal como está.

---

## 1. Qué necesitás instalado

| Herramienta | Para qué sirve |
|-------------|----------------|
| **Git** | Clonar el repositorio. |
| **Docker Desktop** (Windows/macOS) o **Docker Engine + Compose plugin** (Linux) | Levantar Postgres y los cuatro servicios con un solo comando. |
| **Python 3.12** + **Node.js 20** | Solo si vas a correr tests o el frontend en la máquina sin Docker. |
| **kubectl** + **Helm 3.14+** | Despliegue en Kubernetes (AKS u otro). |

Comprobaciones rápidas:

```bash
git --version
docker version
docker compose version
```

En Windows, Docker Desktop debe estar **encendido** antes de `docker compose`; si ves errores del tipo “pipe dockerDesktopLinuxEngine”, el daemon no está corriendo o WSL2 no está bien enlazado.

---

## 2. Arranque local (recomendado): Docker Compose

Desde la **raíz del repo** (donde está `docker-compose.yml`):

```bash
docker compose up --build
```

La primera vez descarga imágenes base y construye; puede tardar varios minutos.

### 2.1 Cómo saber si todo está bien

- En la consola no deberían quedar contenedores en reinicio infinito (`Restarting`).
- Abrí en el navegador:

| Qué | URL |
|-----|-----|
| **Interfaz web** | http://localhost:3000 |
| Documentación API BFF (Swagger) | http://localhost:8080/docs |
| market-data | http://localhost:8001/docs |
| signal-engine | http://localhost:8002/docs |

### 2.2 Probar sin el navegador

```bash
curl "http://localhost:8080/api/v1/summary?symbol=AAPL"
```

Deberías recibir JSON con `prices` (serie mock) y `signal` (BUY / SELL / HOLD y motivos).

### 2.3 Parar el entorno

En la misma terminal: `Ctrl+C`. Para borrar contenedores y red:

```bash
docker compose down
```

Los datos de Postgres se pierden salvo que configures un volumen nombrado (el MVP actual no persiste datos entre `down -v` si agregás el flag `-v`).

---

## 3. Desarrollo local sin Docker (opcional)

Útil para depurar un solo servicio.

### 3.1 PostgreSQL

Necesitás una instancia Postgres accesible en `localhost:5432` con:

- Usuario: `signals`
- Contraseña: `signals`
- Base: `signals`

(O ajustá la variable `DATABASE_URL` en `signal-engine`.)

### 3.2 market-data

```bash
cd services/market-data
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### 3.3 signal-engine

En otra terminal, con el mismo venv o uno nuevo:

```bash
cd services/signal-engine
pip install -r requirements.txt
set MARKET_DATA_BASE_URL=http://127.0.0.1:8001
set DATABASE_URL=postgresql+asyncpg://signals:signals@127.0.0.1:5432/signals
uvicorn app.main:app --reload --port 8002
```

(Linux/macOS: `export` en lugar de `set`.)

### 3.4 api-bff

```bash
cd services/api-bff
pip install -r requirements.txt
set MARKET_DATA_BASE_URL=http://127.0.0.1:8001
set SIGNAL_ENGINE_BASE_URL=http://127.0.0.1:8002
uvicorn app.main:app --reload --port 8080
```

### 3.5 web-ui

```bash
cd web-ui
npm install
npm run dev
```

El `vite.config.ts` ya proxifica `/api` hacia `http://localhost:8080`. Abrí http://localhost:5173.

### 3.6 Tests Python

Desde la raíz del repo:

```bash
pip install ruff pytest
ruff check services/market-data/app services/signal-engine/app services/api-bff/app
cd services/market-data && pytest -q
cd ../signal-engine && pytest -q
cd ../api-bff && pytest -q
```

---

## 4. Imágenes para Kubernetes (ghcr.io)

El chart Helm espera imágenes en `charts/signals-platform/values.yaml` (por defecto `ghcr.io/example/...`). **Tenés que cambiarlas** a tu organización o usuario de GitHub, por ejemplo:

```yaml
images:
  marketData: ghcr.io/MI_ORG/signals-market-data:v0.1.0
  signalEngine: ghcr.io/MI_ORG/signals-signal-engine:v0.1.0
  apiBff: ghcr.io/MI_ORG/signals-api-bff:v0.1.0
  webUi: ghcr.io/MI_ORG/signals-web-ui:v0.1.0
```

### 4.1 Opción A: Release automático (GitHub Actions)

1. En GitHub: **Settings → Actions → General** → permitir que los workflows tengan permisos para **Packages** si hace falta.
2. Creá un tag semver y pushealo:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. El workflow `.github/workflows/release.yml` construye y sube las cuatro imágenes a **ghcr.io** y adjunta el `.tgz` del chart al **Release**.

4. Copiá los tags exactos que generó el release y pegalos en `values.yaml`.

### 4.2 Opción B: Build manual

Con sesión iniciada en ghcr (`docker login ghcr.io`):

```bash
docker build -t ghcr.io/MI_ORG/signals-market-data:dev ./services/market-data
docker push ghcr.io/MI_ORG/signals-market-data:dev
# repetir para signal-engine, api-bff, web-ui
```

Si el paquete es **privado**, en el cluster creá un `imagePullSecret` y referenciálo en `values.yaml` bajo `imagePullSecrets`.

---

## 5. Despliegue en Kubernetes (Helm)

Resumen; el detalle operativo está en [runbook.md](runbook.md).

1. **Cluster** (por ejemplo AKS) y `kubectl` apuntando al contexto correcto.
2. **Ingress NGINX** instalado en el cluster (ver comandos en `runbook.md`).
3. **Dependencias del chart:**

   ```bash
   cd charts/signals-platform
   helm dependency update
   cd ../..
   ```

   Requiere internet para bajar el subchart de PostgreSQL de Bitnami.

4. **Namespace** (opcional, ya definido en el repo):

   ```bash
   kubectl apply -f deploy/namespaces.yaml
   ```

5. **Instalar / actualizar:**

   ```bash
   helm upgrade --install signals ./charts/signals-platform \
     --namespace signals-dev \
     --create-namespace \
     -f charts/signals-platform/values.yaml
   ```

6. **Nombre del servicio UI** para port-forward: si el release se llama `signals`, el servicio de la UI suele ser `signals-signals-platform-web-ui` (prefijo `release` + nombre del chart). Verificá con:

   ```bash
   kubectl get svc -n signals-dev
   ```

7. **Ingress:** ajustá `ingress.host` en `values.yaml` a un host que puedas resolver (por ejemplo entrada en `/etc/hosts` hacia la IP externa del controlador ingress).

---

## 6. Monitoreo (Prometheus y Grafana)

Los backends exponen `/metrics`. En el chart, los `Service` llevan anotaciones `prometheus.io/*` para descubrimiento clásico.

- Cómo importar el dashboard JSON: [monitoring/README.md](../monitoring/README.md).
- Archivo del dashboard: `monitoring/grafana/dashboards/signals-overview.json`.

---

## 7. Problemas frecuentes

| Síntoma | Qué revisar |
|---------|-------------|
| `docker compose` falla al conectar con el daemon | Docker Desktop encendido; en Windows, modo Linux containers si aplica. |
| `signal-engine` devuelve 502 / “market_data_unavailable” | Que `market-data` esté arriba y que `MARKET_DATA_BASE_URL` apunte al nombre correcto del servicio (en Compose: `http://market-data:8000`). |
| Error de conexión a Postgres | En Compose, `signal-engine` depende del healthcheck de `postgres`; esperá unos segundos tras el arranque. |
| Helm: error al `dependency update` | Red, versión del subchart en `Chart.yaml`, o repositorio Bitnami bloqueado. |
| Imágenes `ImagePullBackOff` | Tags incorrectos en `values.yaml`; registry privado sin `imagePullSecret`. |
| UI en K8s sin datos en `/api` | El ConfigMap de nginx del chart debe apuntar al servicio del BFF; revisá `kubectl logs` del pod `web-ui`. |

---

## 8. Documentación relacionada

- [runbook.md](runbook.md) — comandos Helm, Ingress, port-forward, CI.
- [architecture.md](architecture.md) — diagrama y responsabilidades.
- [api-contract.md](api-contract.md) — contrato JSON entre servicios.
- [evidence/README.md](evidence/README.md) — checklist para la entrega.

Si algo no coincide con tu entorno (por ejemplo otro namespace o otro nombre de release), decime qué error exacto ves y lo encaminamos.

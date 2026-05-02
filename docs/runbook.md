# Runbook operativo

## Local con Docker Compose

```bash
docker compose up --build
```

| Servicio       | URL |
|----------------|-----|
| UI             | http://localhost:3000 |
| api-bff        | http://localhost:8080/docs |
| market-data    | http://localhost:8001/docs |
| signal-engine  | http://localhost:8002/docs |
| PostgreSQL     | localhost:5432 (usuario/clave `signals`/`signals`) |

Prueba rápida de API agregada:

```bash
curl "http://localhost:8080/api/v1/summary?symbol=AAPL"
```

## Helm (Kubernetes)

### Prerrequisitos

- `kubectl` configurado contra el cluster (por ejemplo **AKS**).
- [Helm](https://helm.sh/) 3.14+.
- Ingress Controller **NGINX** instalado en el cluster (común en AKS con Helm oficial de ingress-nginx).

### Dependencias del chart

```bash
cd charts/signals-platform
helm dependency update
cd ../..
```

Descarga el subchart de **Bitnami PostgreSQL** definido en `Chart.yaml`.

### Imágenes

1. Actualizar `charts/signals-platform/values.yaml` → claves `images.*` con vuestro `ghcr.io/<org>/...` (tras CI release o build manual).
2. Si el registry es privado, crear `imagePullSecret` en el namespace y referenciarlo en `imagePullSecrets` del values.

### Instalación

```bash
kubectl apply -f deploy/namespaces.yaml
helm upgrade --install signals ./charts/signals-platform \
  --namespace signals-dev \
  --create-namespace \
  -f charts/signals-platform/values.yaml
```

### Ingress en AKS

1. Instalar ingress-nginx (ejemplo, revisar versión en documentación oficial):

   ```bash
   helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
   helm repo update
   helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
     --namespace ingress-nginx --create-namespace
   ```

2. Obtener IP externa del servicio `ingress-nginx-controller` y mapear el host configurado en `values.yaml` (`ingress.host`) en `/etc/hosts` o DNS de curso.

3. Verificar:

   ```bash
   kubectl get ingress -n signals-dev
   ```

### Port-forward (sin Ingress)

```bash
kubectl port-forward -n signals-dev svc/<release>-signals-platform-web-ui 3000:80
```

Sustituir `<release>` por el nombre del release de Helm (por defecto `signals` → prefijo de recursos según plantillas).

### Actualización

```bash
helm upgrade signals ./charts/signals-platform -n signals-dev -f charts/signals-platform/values.yaml
helm history signals -n signals-dev
```

## CI/CD

Los workflows de GitHub Actions están en `.github/workflows/`. El release por tag `v*.*.*` publica imágenes en **ghcr.io** y adjunta el paquete Helm al GitHub Release.

## Monitoreo

Ver [monitoring/README.md](../monitoring/README.md).

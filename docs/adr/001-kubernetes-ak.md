# ADR 001 — Kubernetes administrado en Azure (AKS)

## Estado

Aceptado — alcance académico MVP (3 semanas, 2 personas).

## Contexto

La actividad exige Kubernetes administrado entre **EKS, AKS, GKE u OpenShift**, con presión de **costo bajo** y **entrega rápida**.

## Decisión

Usar **Azure Kubernetes Service (AKS)** como servicio administrado principal.

## Consecuencias

### Positivas

- Coste operativo típicamente centrado en **nodos**; el plano de control de AKS no introduce el cargo frecuente de control plane de **EKS**, lo que ayuda en proyectos cortos con presupuesto ajustado.
- Integración razonable con flujos de estudiantes (Azure for Students, documentación unificada).
- Compatible con **Helm**, **Ingress NGINX**, **Prometheus/Grafana** estándar de Kubernetes.

### Negativas / riesgos

- Curva inicial de **Azure RBAC / redes** si el equipo no conoce Azure.
- Coste de **Load Balancer**, discos y egress si se dejan recursos encendidos 24/7.

## Alternativas descartadas (resumen)

- **Amazon EKS**: potente, pero el coste del control plane suele penalizar MVPs académicos de corta duración.
- **Google GKE**: muy sólido; elección equivalente si el equipo ya dispone de créditos GCP y experiencia.
- **Red Hat OpenShift**: más peso operativo y coste para un MVP de demostración.

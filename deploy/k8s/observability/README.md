# Week-9 Observability Wiring

This package wires the ACOS SLO dashboard and alert rules into a Kubernetes observability stack.

## Included Assets
1. `kustomization.yaml`: generates a Grafana dashboard ConfigMap from `docs/observability/grafana_slo_dashboard.json`.
2. `prometheus-rule-slo-alerts.yaml`: Prometheus alert rules for availability burn, p95 latency, and tenant error rate.

## Deploy
```powershell
kubectl apply -k deploy/k8s/observability
```

## Validate
Generate an evidence report:

```powershell
python scripts/verify_week9_observability_assets.py
```

The script writes a pass/fail JSON report to `deploy/k8s/observability/evidence/`.

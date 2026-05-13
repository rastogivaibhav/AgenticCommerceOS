# Week 10 Performance Baseline

## Execution Timestamp
- `2026-04-09T09:14:27.0287303Z`

## Evidence Artifact
- `deploy/k8s/performance/evidence/week10-performance-baseline-20260409-091427.json`

## Test Configuration
- Base URL: `http://localhost:8082`
- Single-tenant sample: `60` requests (`tenant_id=default`)
- Mixed-tenant sample: `120` requests (`tenant_id=default` and `tenant_id=eu-store`, alternating)
- Inter-scenario cooldown: `65` seconds

## Summary
- Overall pass: `true`
- Pass rule: each scenario error rate `< 2.0%`
- Observed HTTP status: `200` only in both scenarios

## Baseline Metrics

| Scenario | Requests | Success | Error Rate | Throughput (RPS) | p50 (ms) | p95 (ms) | p99 (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| single_tenant_default | 60 | 60 | 0.0% | 2.434 | 375.463 | 553.333 | 1180.467 |
| mixed_tenant_default_eu_store | 120 | 120 | 0.0% | 3.595 | 244.648 | 436.394 | 824.878 |

## Tenant Breakdown (Mixed Scenario)
- `default`: 60/60 success, p95=`434.106 ms`
- `eu-store`: 60/60 success, p95=`436.394 ms`

## Notes
- Baseline run used a temporary shopper instance on `8082` to avoid local `8080` conflicts.
- Global journey limiter was raised for baseline execution to avoid masking tenant-level behavior during sample collection.

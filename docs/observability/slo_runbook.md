# SLO Runbook (Week 9 Baseline)

## Scope
This runbook defines baseline SLO monitoring for ACOS journeys with tenant-level visibility.

## Core SLOs
1. Availability: `>= 99.0%` successful journey executions per rolling 60 minutes.
2. Latency P95: `<= 2000 ms` per journey type (rolling 60 minutes).
3. Error rate: `<= 1.0%` per tenant (rolling 60 minutes).

## Signals
1. Prometheus metrics from `/metrics`:
   - `acos_journey_requests_total`
   - `acos_journey_duration_seconds`
   - `acos_api_errors_total`
2. Trace envelope events from `/analytics/traces`:
   - `tenant_id`
   - `run_id`
   - `workflow_id`
   - `trace_id`
3. SLO snapshot from `/analytics/slo`.

## Alert Rules (Week-9 Wiring)
1. `AcosJourneyAvailabilityBurn`: triggers when failed-journey burn rate exceeds 1% for 15 minutes.
2. `AcosJourneyLatencyP95High`: triggers when p95 latency exceeds 2000ms for 10 minutes.
3. `AcosTenantErrorRateHigh`: triggers when any tenant error rate exceeds 1% for 10 minutes.

Rule pack path: `deploy/k8s/observability/prometheus-rule-slo-alerts.yaml`.

## Alert Triage
1. Check `/analytics/slo?tenant_id=<id>&window_minutes=60`.
2. Pull recent traces: `/analytics/traces?tenant_id=<id>&limit=200`.
3. Correlate failed `run_id` with workflow promotion events and connector degradation (`_connector.degraded`).
4. If error spike is connector-driven, force local mode in tenant connector config and re-check SLO.

## Immediate Mitigations
1. Route affected tenant connectors to local mode.
2. Roll back active workflow version if failure started post-promotion.
3. Apply temporary rate-limit for noisy tenant traffic if p95 saturation occurs.

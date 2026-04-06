# ACOS Go-Live Runbook

## Go-Live Date

**Target:** 2026-04-15T06:00:00Z (UTC)
**Backup Date:** 2026-04-16 (in case of blocking issues)

## Pre-Go-Live Checklist (T-24 hours)

- [ ] All sign-offs collected on production gate evidence pack
- [ ] Operations and support teams briefed
- [ ] Incident commander designated
- [ ] On-call schedule activated
- [ ] Monitoring dashboards verified and active
- [ ] Rollback procedure tested
- [ ] Customer communication drafted (if applicable)
- [ ] Database backups current
- [ ] Docker images pushed to registry

## Go-Live Sequence

### Phase 1: Pre-Flight (06:00 - 06:15 UTC)

1. **Incident Commander** opens #acos-go-live Slack channel
2. **Platform Engineer** verifies all services healthy
   - API: `curl http://acos-api:8000/health`
   - Database: Test connections
   - Monitoring: Grafana dashboards loading
3. **Workflow Administrator** verifies pilot workflows loaded in prod environment
4. **Risk & Compliance Owner** confirms approval queue empty (no pending changes)

### Phase 2: Observation Mode (06:15 - 06:30 UTC)

1. **Platform Engineer** enables observation mode (logs only, no traffic routing)
2. **Monitoring Team** watches error rate and latency
3. **Duration:** 15 minutes minimum before proceeding to Phase 3

### Phase 3: Canary Traffic (06:30 - 07:00 UTC)

1. **Platform Engineer** routes 5% traffic to discovery workflow
2. **Monitoring Team** watches for:
   - Error rate increase
   - Latency spikes
   - Unusual log patterns
3. **Success Criterion:** No critical errors, error rate < 1%
4. **Abort Criterion:** Error rate > 2%, P99 latency > 2000ms

### Phase 4: Ramp (07:00 - 08:00 UTC)

1. **Platform Engineer** gradually increases traffic:
   - 10% discovery (07:00)
   - 20% discovery + 5% post_purchase (07:15)
   - 50% discovery + 10% post_purchase (07:30)
   - 100% discovery + 50% post_purchase (07:45)
   - 100% discovery + 100% post_purchase (08:00)
2. **Monitoring Team** continues watching metrics
3. **Operations Lead** monitors customer impact (if applicable)

### Phase 5: Full Operations (08:00+ UTC)

1. **All workflows** active at 100% traffic
2. **Standard on-call procedures** activate
3. **Incident Commander** closes war room (if all healthy)

## Abort Procedure

If critical issues detected:

1. **Platform Engineer** immediately pauses affected workflow
2. **Incident Commander** calls "ABORT"
3. **Platform Engineer** executes rollback (see RUNBOOK_ROLLBACK.md)
4. **Post-Incident Review** scheduled within 24 hours

## Post-Go-Live (T+24 hours)

- [ ] Error rate stable and < 0.5%
- [ ] No critical incidents
- [ ] Customer feedback positive (if applicable)
- [ ] All workflows operational
- [ ] Performance within baselines

---

## Contacts

| Role | Name | Contact | Timezone |
|---|---|---|---|
| Incident Commander | [Name] | Slack @oncall | UTC |
| Platform Engineer (On-Call) | [Name] | Phone/Slack | UTC |
| Workflow Admin (On-Call) | [Name] | Phone/Slack | UTC |
| Operations Lead | [Name] | Slack @ops-lead | UTC |
| Risk & Compliance | [Name] | Slack @risk-owner | UTC |

---

## Rollback Trigger

**Automatic Rollback Conditions:**
- Error rate > 5% for 5+ minutes
- P99 latency > 3000ms for 5+ minutes
- Database query failures > 10%

**Manual Rollback Reasons:**
- Compliance violation detected
- Data loss or corruption detected
- Customer escalation requiring rollback

---

## Post-Go-Live Monitoring

See: `docs/RUNBOOK_MONITORING.md`

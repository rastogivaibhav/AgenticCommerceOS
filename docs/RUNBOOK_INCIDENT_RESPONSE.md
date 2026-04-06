# ACOS Incident Response Runbook

## Severity Levels

| Level | Detection | Response Time | Escalation |
|---|---|---|---|
| **P1** | Automated alert (error rate > 5%) | 30 min | CTO |
| **P2** | Manual detection | 2 hours | Engineering Manager |
| **P3** | Log review | 4 hours | Team Lead |

## Incident Declaration

**Open War Room:**
```bash
#acos-incident-response (Slack)
```

**Gather Key Info:**
- Incident detection time
- Affected workflow(s)
- Affected tenant(s)
- Error message(s)
- User impact (if known)

## Incident Investigation

### Step 1: Assess Severity

1. **Check error rate:** `curl acos-api:8000/health/workflows`
2. **Check affected users:** How many customers impacted?
3. **Declare severity level:** P1 / P2 / P3

### Step 2: Gather Evidence

1. **Error logs:** `kubectl logs deployment/acos-api -f --tail=200`
2. **Metrics:** Check Grafana dashboard
3. **Database:** Run diagnostic queries
4. **Recent changes:** Check promotion history

### Step 3: Triage

| Diagnosis | Action |
|---|---|
| Workflow logic error | Pause workflow, escalate to workflow author |
| Connector/API failure | Activate failsafe, escalate to connector owner |
| Database issue | Database team investigates |
| Deployment/infrastructure | Platform engineering investigates |

## Response Actions

### Action 1: Pause Workflow (Immediate)

```bash
curl -X POST http://acos-api:8000/api/workflows/{workflow_id}/pause \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"incident_id": "INC-001", "reason": "Error rate spike"}'
```

**Effect:** Stops processing new requests, existing requests continue.

### Action 2: Activate Failsafe (If Available)

```bash
curl -X POST http://acos-api:8000/api/workflows/{workflow_id}/failsafe \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"incident_id": "INC-001"}'
```

**Effect:** Routes requests to fallback handler (e.g., human routing).

### Action 3: Execute Rollback (If Needed)

```bash
curl -X POST http://acos-api:8000/api/workflows/{workflow_id}/rollback \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"incident_id": "INC-001", "target_version": "1.0.0"}'
```

**Effect:** Reverts to prior stable version.

---

## Incident Timeline

**T+0:** Incident detected
- Action: Declare severity, open war room
- Owner: Incident Commander

**T+5min:** Assessment complete
- Action: Pause affected workflows if needed
- Owner: Platform Engineer

**T+15min:** Root cause identified
- Action: Execute remediation (failsafe/rollback)
- Owner: Platform Engineer + Workflow Owner

**T+30min:** Incident resolved
- Action: Monitor health, resume workflows gradually
- Owner: Ops Lead

**T+24h:** Post-incident review
- Action: Document root cause, create follow-up tickets
- Owner: Incident Commander + Engineering Lead

---

## Rollback Procedure

1. **Verify rollback target:** `curl .../workflows/{id}/rollback-targets`
2. **Confirm with stakeholders:** Engineering + Risk + Ops leads
3. **Execute rollback:** (see Action 3 above)
4. **Monitor recovery:** Watch error rate and latency
5. **Verify data integrity:** Check for data loss

---

## Customer Communication

If incident impacts customers:

1. **Status page update:** Notify of detected issue
2. **Slack #customer-incidents:** Brief on impact and ETA
3. **Affected customers email:** Personal outreach for P1 incidents
4. **Post-incident summary:** Published within 24 hours

---

## Escalation Matrix

```
Issue Unresolved After 15min → Escalate to: Platform Manager
Issue Unresolved After 45min → Escalate to: Director of Engineering
Issue Unresolved After 2h → Escalate to: CTO
```

---

## Learning Review

**Scheduled:** Within 24 hours of incident resolution

**Topics:**
- Root cause summary
- Detection gaps
- Response improvements
- Prevention measures

**Output:**
- Incident ticket with action items
- Documentation updates
- Team training (if needed)

---

## Contacts (On-Call)

| Role | Name | Phone | Slack |
|---|---|---|---|
| Incident Commander | @oncall-ic | [Phone] | @ic |
| Platform Engineer | @oncall-eng | [Phone] | @eng-on-call |
| Database Admin | @oncall-dba | [Phone] | @dba-on-call |
| Operations Lead | @oncall-ops | [Phone] | @ops-on-call |

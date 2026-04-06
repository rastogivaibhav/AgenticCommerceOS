# ACOS Workflow Promotion Runbook

## Overview

This runbook describes the safe, governed process for promoting workflows from dev → test → stage → prod.

## Promotion Request Form

**Requestor:** _________________
**Workflow ID:** _________________
**Target Version:** _________________
**Target Environment:** dev / test / stage / prod
**Reason:** _________________

## Promotion Checklist

### Pre-Promotion (in source environment)

- [ ] Code reviewed and approved
- [ ] All unit tests passing: `pytest tests/unit/ -v`
- [ ] Integration tests passing: `pytest tests/integration/ -v`
- [ ] Schema validation passing
- [ ] Audit coverage present
- [ ] Rollback plan documented

### Promotion Request (in control plane UI)

1. **Workflow Admin** opens workflow detail
2. **Click "Promote"** button
3. **Select target environment:** test / stage / prod
4. **Review diff:** Verify only intended changes
5. **Add promotion reason**
6. **Submit for approval**

### Approval Process (if required)

**Dev → Test:** Workflow Admin can approve
**Test → Stage:** Engineering Owner approval required
**Stage → Prod:** Risk & Compliance Owner approval required

**Risk Owner Review:**
- [ ] Changes align with policy guardrails
- [ ] Financial thresholds within bounds
- [ ] Audit coverage complete
- [ ] Rollback plan viable

### Promotion Execution

1. **Workflow Admin** clicks "Approve" (if authorized)
2. **Promotion begins** - workflow version promoted to target environment
3. **Audit event created** - promotion logged with metadata
4. **Health monitoring activated** - watch for issues in target environment
5. **Promotion complete** - workflow active in target environment

### Post-Promotion (monitoring)

- [ ] Error rate normal in target environment
- [ ] Latency within baselines
- [ ] No policy violations triggered
- [ ] Audit trail complete

---

## Rollback from Failed Promotion

If issues detected after promotion:

1. **Operations Lead** identifies issue
2. **Platform Engineer** clicks "Rollback" on workflow detail
3. **Select prior version:** (automatically populated)
4. **Confirm rollback reason**
5. **Rollback executes** - workflow reverted to previous version
6. **Incident review** scheduled within 2 hours

---

## Promotion History

Each workflow maintains promotion history:

```
Workflow: discovery_v1
├─ 2026-04-01 10:00 → test (Approved by: jsmith)
├─ 2026-04-03 14:00 → stage (Approved by: rjones)
├─ 2026-04-10 08:00 → prod (Approved by: mwilson)
└─ 2026-04-15 06:30 Active in: prod
```

---

## Common Issues

### "Promotion Blocked: Policy Violation"
- Review workflow definition for policy guardrails
- Adjust thresholds if needed
- Contact Risk Owner for override

### "Promotion Failed: Migration Error"
- Check database migration logs
- Rollback workflow to previous version
- File incident ticket

### "Promotion Pending: Awaiting Approval"
- Verify approval request sent to correct owner
- Follow up on approval ticket
- Provide additional context if needed

---

## Contacts

- **Workflow Admin:** workflow-admins@company.com
- **Engineering Owner:** eng-lead@company.com
- **Risk & Compliance:** risk-owner@company.com

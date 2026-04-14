import { test, expect } from './fixtures/index.js';

/**
 * Suite 1: Workflow Lifecycle
 *
 * Proves that the full draft → approve → promote lifecycle:
 *   1. Calls the correct versioned API routes
 *   2. Returns the expected lifecycle_state at each step
 *   3. Writes a workflow row with status="active" to the DB
 *   4. Writes ≥ 3 audit_events rows for the workflow
 *
 * Routes used:
 *   POST /api/v1/workflows
 *   POST /api/v1/workflows/{id}/versions/{v}/approve
 *   POST /api/v1/workflows/{id}/versions/{v}/promote
 *   DELETE /api/v1/workflows/{id}          ← cleanup (archives)
 *
 * DB assertions:
 *   SELECT status FROM workflows WHERE id=$1             → "active"
 *   SELECT COUNT(*) FROM audit_events WHERE resource_type='workflow' AND resource_id=$1 → ≥ 3
 */

test.beforeAll(async ({ request }) => {
  const res = await request.get('http://localhost:8081/');
  if (res.status() >= 500) {
    throw new Error('Ops API is not healthy. Run "docker compose up -d" and retry.');
  }
});

test('workflow draft → approve → promote writes correct state to DB with audit trail', async ({
  request,
  authHeaders,
  db,
}) => {
  const uniqueName = `e2e-lifecycle-${crypto.randomUUID().slice(0, 8)}`;
  let workflowId = null;

  // ── 1. Create draft ──────────────────────────────────────────────────────────
  const createRes = await request.post('http://localhost:8081/api/v1/workflows', {
    headers: authHeaders,
    data: {
      name: uniqueName,
      workflow_family: 'service',
      tenant_id: 'default',
      change_summary: 'E2E test draft',
    },
  });
  expect(createRes.status(), 'Create workflow should return 200').toBe(200);

  const created = await createRes.json();
  workflowId = created.workflow.id;
  const version = created.version.version; // e.g. "v1"

  expect(created.workflow.status, 'Newly created workflow should be draft').toBe('draft');
  expect(created.version.lifecycle_state, 'Newly created version should be draft').toBe('draft');

  try {
    // ── 2. Approve ────────────────────────────────────────────────────────────
    const approveRes = await request.post(
      `http://localhost:8081/api/v1/workflows/${workflowId}/versions/${version}/approve`,
      {
        headers: authHeaders,
        data: { approval_note: 'e2e approval' },
      }
    );
    expect(approveRes.status(), 'Approve should return 200').toBe(200);

    const approved = await approveRes.json();
    expect(approved.version.lifecycle_state, 'Approved version should have lifecycle_state=approved').toBe('approved');

    // ── 3. Promote ────────────────────────────────────────────────────────────
    const promoteRes = await request.post(
      `http://localhost:8081/api/v1/workflows/${workflowId}/versions/${version}/promote`,
      {
        headers: authHeaders,
        data: { target_environment: 'dev', approval_note: 'e2e promote' },
      }
    );
    expect(promoteRes.status(), 'Promote should return 200').toBe(200);

    const promoted = await promoteRes.json();
    expect(promoted.version.lifecycle_state, 'Promoted version should have lifecycle_state=active').toBe('active');

    // ── 4. DB: workflow.status should be "active" ─────────────────────────────
    const wfRows = await db.query('SELECT status FROM workflows WHERE id=$1', [workflowId]);
    expect(wfRows.length, 'Workflow row should exist in DB').toBe(1);
    expect(wfRows[0].status, 'Workflow status in DB should be active after promote').toBe('active');

    // ── 5. DB: audit trail should have ≥ 3 entries ───────────────────────────
    const auditRows = await db.query(
      "SELECT COUNT(*)::int AS cnt FROM audit_events WHERE resource_type='workflow' AND resource_id=$1",
      [workflowId]
    );
    expect(auditRows[0].cnt, 'Audit trail should have at least 3 events (create, approve, promote)').toBeGreaterThanOrEqual(3);

  } finally {
    // ── Cleanup: archive the workflow ─────────────────────────────────────────
    if (workflowId) {
      await request.delete(`http://localhost:8081/api/v1/workflows/${workflowId}`, {
        headers: authHeaders,
      });
    }
  }
});

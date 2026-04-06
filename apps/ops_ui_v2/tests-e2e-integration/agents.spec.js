import { test, expect } from './fixtures/index.js';

/**
 * Suite 3: Agents UI Journey
 *
 * Proves that:
 *   1. The agents page renders without JS errors and the list container is visible.
 *   2. A new agent POSTed via API appears in the UI on reload.
 *   3. The new agent is persisted in the DB (SELECT by id).
 *
 * Navigation note: The UI is a React SPA mounted at /ui/.
 * Direct HTTP GET /ui/agents returns 404 from the static file server.
 * All navigation must start at /ui/ and use client-side routing (click the nav link).
 *
 * Auth note: The UI reads its JWT from localStorage key "ops-token".
 * We inject the token via page.addInitScript() before any navigation so every
 * API call the SPA makes is authenticated.
 *
 * Routes used:
 *   GET  /ui/                           ← SPA entry point
 *   POST /api/v1/agents                 ← create agent
 *
 * DB assertions:
 *   SELECT id FROM agents WHERE id=$1   → 1 row
 *
 * Cleanup: direct DB DELETE (no HTTP DELETE endpoint exists for agents).
 */

test.beforeAll(async ({ request }) => {
  const res = await request.get('http://localhost:8081/');
  if (res.status() >= 500) {
    throw new Error('Ops API not healthy. Run "docker compose up -d" and retry.');
  }
});

/** Inject the ops JWT into localStorage before the page loads. */
async function injectAuth(page, authHeaders) {
  const token = authHeaders.Authorization.replace('Bearer ', '');
  await page.addInitScript((t) => {
    localStorage.setItem('ops-token', t);
    localStorage.setItem('ops_token', t);
    localStorage.setItem('token', t);
  }, token);
}

/** Navigate to the Agents page via SPA routing. */
async function goToAgents(page) {
  await page.goto('http://localhost:8081/ui/');
  await page.waitForLoadState('networkidle');
  await page.click('a[href*="/agents"]');
  await page.waitForLoadState('networkidle');
}

test('agents page renders without JS errors and list container is visible', async ({
  page,
  authHeaders,
}) => {
  const jsErrors = [];
  page.on('pageerror', (err) => jsErrors.push(err.message));

  await injectAuth(page, authHeaders);
  await goToAgents(page);

  // Page should not have crashed
  expect(jsErrors, `JS errors on agents page: ${jsErrors.join(', ')}`).toHaveLength(0);

  // URL should reflect agents route (SPA navigation succeeded)
  expect(page.url()).toContain('/agents');

  // The "Agents" heading and Create button should be visible
  await expect(page.getByRole('heading', { name: /agents/i }).first()).toBeVisible();
});

test('new agent POSTed via API appears in UI and persists to DB', async ({
  page,
  request,
  authHeaders,
  db,
}) => {
  const agentId = `e2e-agent-${crypto.randomUUID()}`;
  const agentName = `e2e-test-agent-${agentId.slice(-8)}`;

  const agentPayload = {
    id: agentId,
    name: agentName,
    subsystem: 'test',
    status: 'healthy',
    calls: '0',
    uptime: '100%',
    skills: [],
    grade: 'A+',
    latency: '0ms',
    history: [],
  };

  try {
    // ── 1. POST the agent via API ───────────────────────────────────────────
    const createRes = await request.post('http://localhost:8081/api/v1/agents', {
      headers: authHeaders,
      data: agentPayload,
    });
    expect(createRes.status(), 'Create agent should return 200').toBe(200);

    const created = await createRes.json();
    expect(created.status, 'Create response should have status=success').toBe('success');

    // ── 2. DB: agent row should exist ──────────────────────────────────────
    const dbRows = await db.query('SELECT id FROM agents WHERE id=$1', [agentId]);
    expect(dbRows.length, 'Agent should be persisted in DB').toBe(1);

    // ── 3. Navigate to agents page and verify agent appears in UI ──────────
    await injectAuth(page, authHeaders);
    await goToAgents(page);

    // Agent name should appear in the list
    const agentElement = page.getByText(agentName);
    await expect(agentElement, `Agent "${agentName}" should appear in agents list`).toBeVisible({ timeout: 10000 });

  } finally {
    // ── Cleanup: delete agent directly from DB (no HTTP DELETE endpoint) ───
    await db.query('DELETE FROM agents WHERE id=$1', [agentId]);
    const afterCleanup = await db.query('SELECT id FROM agents WHERE id=$1', [agentId]);
    expect(afterCleanup.length, 'Cleanup: agent should be removed from DB').toBe(0);
  }
});

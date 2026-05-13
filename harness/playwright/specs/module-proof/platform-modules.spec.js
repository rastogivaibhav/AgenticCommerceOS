import { test, expect } from '@playwright/test';
import { makeHeaders } from '../integration/fixtures/auth.js';

const OPS_BASE = process.env.OPS_BASE_URL || 'http://localhost:8081';
const SHOPPER_BASE = process.env.SHOPPER_BASE_URL || 'http://localhost:8080';
const CHAT_BASE = process.env.CHAT_BASE_URL || 'http://localhost:8001';

async function isHealthy(request, url) {
  try {
    const res = await request.get(url, { timeout: 5000 });
    return res.ok();
  } catch {
    return false;
  }
}

test.describe('ACOS Real-World Module Proof', () => {
  test('shopper-api health and journey execution proof', async ({ request }) => {
    test.skip(!(await isHealthy(request, `${SHOPPER_BASE}/health`)), 'shopper-api is not reachable');

    const health = await request.get(`${SHOPPER_BASE}/health`);
    expect(health.status()).toBe(200);
    const healthBody = await health.json();
    expect(healthBody.service).toBe('shopper-api');

    const journey = await request.post(`${SHOPPER_BASE}/v1/journey`, {
      headers: {
        'X-API-Key': process.env.SHOPPER_API_KEY || 'dev-key-insecure',
        'Content-Type': 'application/json',
      },
      data: {
        tenant_id: 'default',
        workflow_family: 'service',
        message: 'Where is my order ORD-1001?',
        customer_id: 'e2e-module-proof',
      },
    });
    expect(journey.status()).toBe(200);
    const body = await journey.json();
    expect(body).toHaveProperty('result');
  });

  test('ops-api health and governed workflow inventory proof', async ({ request }) => {
    test.skip(!(await isHealthy(request, `${OPS_BASE}/health`)), 'ops-api is not reachable');

    const health = await request.get(`${OPS_BASE}/health`);
    expect(health.status()).toBe(200);
    const healthBody = await health.json();
    expect(healthBody.service).toBe('ops-api');

    const { authHeaders } = await makeHeaders();
    const workflows = await request.get(`${OPS_BASE}/api/v1/workflows`, { headers: authHeaders });
    expect(workflows.status()).toBe(200);
    const payload = await workflows.json();
    expect(Array.isArray(payload.workflows)).toBeTruthy();
  });

  test('chat-api security and execution route proof', async ({ request }) => {
    test.skip(!(await isHealthy(request, `${CHAT_BASE}/health`)), 'chat-api is not reachable');

    const health = await request.get(`${CHAT_BASE}/health`);
    expect(health.status()).toBe(200);
    const healthBody = await health.json();
    expect(healthBody.service).toBe('chat-api');

    const unauth = await request.post(`${CHAT_BASE}/api/workflows/wf-module-proof/execute-sync`, {
      data: {
        workflow_id: 'wf-module-proof',
        workflow_name: 'module-proof',
        timeout_seconds: 1,
        steps: [],
        input_data: { message: 'test' },
      },
    });
    expect([401, 403]).toContain(unauth.status());

    const authed = await request.post(`${CHAT_BASE}/api/workflows/wf-module-proof/execute-sync`, {
      headers: {
        Authorization: 'Bearer dev-token',
        'Content-Type': 'application/json',
      },
      data: {
        workflow_id: 'wf-module-proof',
        workflow_name: 'module-proof',
        timeout_seconds: 1,
        steps: [],
        input_data: { message: 'test' },
      },
    });
    expect(authed.status()).toBe(200);
    const payload = await authed.json();
    expect(payload.status).toBeTruthy();
  });

  test('ops control-plane UI route and shell proof', async ({ page, request }) => {
    test.skip(!(await isHealthy(request, `${OPS_BASE}/health`)), 'ops-api is not reachable');

    await page.goto(`${OPS_BASE}/ui/`);
    await expect(page.getByText('ACOS', { exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByText(/Workflow Operations|Agent Registry|Operational Analytics/)).toBeVisible();
  });
});

import { test, expect } from '@playwright/test';
import crypto from 'node:crypto';
import { mkdirSync } from 'node:fs';

const OPS_BASE = process.env.OPS_BASE_URL || 'http://127.0.0.1:8081';
const SPREE_BASE = process.env.SPREE_PUBLIC_URL || 'http://127.0.0.1:3000';
const SPREE_TOKEN = process.env.SPREE_BEARER_TOKEN || 'pk_acos_demo_publishable_key';
const OPS_JWT_SECRET = process.env.OPS_JWT_SECRET || 'dev-ops-secret-change-me';
const OUTPUT_DIR = process.env.PLAYWRIGHT_ECOM_OUTPUT || 'output/playwright/ecom-demo';
mkdirSync(OUTPUT_DIR, { recursive: true });

function spreeHeaders() {
  return SPREE_TOKEN ? { 'X-Spree-API-Key': SPREE_TOKEN } : {};
}

async function getActiveCart(request, customerId = 'cust_1001') {
  const response = await request.get(`${OPS_BASE}/api/northstar/customers/${customerId}/active-cart`, {
    timeout: 15000,
    failOnStatusCode: false,
  });
  if (response.status() === 404) return null;
  expect(response.ok(), `Active cart lookup returned HTTP ${response.status()}`).toBeTruthy();
  return response.json();
}

function findValues(value, key, found = []) {
  if (Array.isArray(value)) {
    for (const item of value) findValues(item, key, found);
  } else if (value && typeof value === 'object') {
    for (const [itemKey, itemValue] of Object.entries(value)) {
      if (itemKey === key) found.push(itemValue);
      findValues(itemValue, key, found);
    }
  }
  return found;
}

function b64url(value) {
  return Buffer.from(value).toString('base64url');
}

function opsToken(role = 'admin') {
  const now = Math.floor(Date.now() / 1000);
  const header = b64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = b64url(JSON.stringify({ sub: 'playwright-ecom-demo', role, roles: [role], iat: now, exp: now + 3600 }));
  const signature = crypto.createHmac('sha256', OPS_JWT_SECRET).update(`${header}.${payload}`).digest('base64url');
  return `${header}.${payload}.${signature}`;
}

async function expectReachable(request, url, label) {
  let response;
  try {
    response = await request.get(url, { timeout: 10000 });
  } catch (error) {
    throw new Error(`${label} is not reachable at ${url}. Start the demo stack with make ecom-demo-up. ${error.message}`);
  }
  expect(response.ok(), `${label} returned HTTP ${response.status()} from ${url}`).toBeTruthy();
  return response;
}

test.describe('Real ecommerce agentic demo: ACOS + Spree', () => {
  test('proves Spree is a real running ecommerce backend', async ({ request }) => {
    await expectReachable(request, `${SPREE_BASE}/up`, 'Spree');

    const products = await request.get(`${SPREE_BASE}/api/v3/store/products`, {
      headers: spreeHeaders(),
    });
    expect(products.ok(), `Spree products endpoint returned HTTP ${products.status()}`).toBeTruthy();

    const body = await products.json();
    expect(Array.isArray(body.data)).toBeTruthy();
    expect(body.data.length, 'Spree should expose seeded products through the Store API').toBeGreaterThan(0);

    const firstProduct = body.data[0];
    expect(firstProduct).toHaveProperty('id');
    expect(firstProduct.id, 'Spree product resources should have stable product ids').toBeTruthy();

    await test.info().attach('spree-products.json', {
      body: JSON.stringify({ count: body.data.length, firstProduct }, null, 2),
      contentType: 'application/json',
    });
  });

  test('proves ACOS routes agent tool calls to real Spree', async ({ request }) => {
    await expectReachable(request, `${OPS_BASE}/health`, 'ACOS Ops API');

    const response = await request.post(`${OPS_BASE}/api/northstar/messages`, {
      data: {
        tenant_id: 'default',
        channel: 'web',
        channel_user_id: 'playwright-ecom-demo',
        customer_id: 'cust_1001',
        text: 'Find me a product under 250 and check whether it is available.',
      },
      timeout: 45000,
    });
    expect(response.ok(), `ACOS northstar message returned HTTP ${response.status()}`).toBeTruthy();
    const body = await response.json();
    expect(body.status).toBe('success');

    const sources = [...new Set(findValues(body, 'source'))].sort();
    expect(sources, 'At least one tool result should be sourced from Spree').toContain('spree');

    const toolNames = findValues(body, 'tool_name');
    expect(toolNames).toContain('catalog.search');

    await test.info().attach('acos-spree-journey.json', {
      body: JSON.stringify({
        status: body.status,
        intent: body.intent,
        agent: body.agent,
        sources,
        toolNames,
      }, null, 2),
      contentType: 'application/json',
    });
  });

  test('shows the Ops UI proof journey to a human operator', async ({ page }) => {
    await page.goto(`${OPS_BASE}/dev/auth/bootstrap/admin?redirect=/ui/estate`);
    await expect(page).toHaveURL(/\/ui\/estate/);

    await expect(page.getByRole('main').getByRole('heading', { name: 'Estate Dashboard' })).toBeVisible();

    await page.screenshot({ path: `${OUTPUT_DIR}/01-estate-dashboard.png`, fullPage: true });

    const runProof = page.getByRole('button', { name: 'Run proof journey' });
    await expect(runProof).toBeVisible();
    await runProof.click();

    await expect(page.getByText('Final merged response')).toBeVisible({ timeout: 45000 });
    await expect(page.getByText('No proof journey run in this session')).toHaveCount(0);
    await page.screenshot({ path: `${OUTPUT_DIR}/02-proof-journey-result.png`, fullPage: true });
  });

  test('shows Spree connector health in the Ops connector registry', async ({ request }) => {
    const response = await request.get(`${OPS_BASE}/api/v1/connectors/bindings`, {
      headers: { Authorization: `Bearer ${opsToken()}` },
    });
    expect(response.ok(), `Connector registry returned HTTP ${response.status()}`).toBeTruthy();

    const body = await response.json();
    const bindings = body.bindings || [];
    const spree = bindings.find((binding) => binding.connector_type === 'spree');
    expect(spree, 'Spree connector should appear in Ops connector registry').toBeTruthy();
    expect(spree.mode).toBe('live');
    expect(spree.status).toBe('healthy');
  });

  test('proves web and WhatsApp update the same live Spree cart', async ({ request }) => {
    await expectReachable(request, `${OPS_BASE}/health`, 'ACOS Ops API');
    await expectReachable(request, `${SPREE_BASE}/up`, 'Spree');

    const before = await getActiveCart(request);

    const webResponse = await request.post(`${OPS_BASE}/api/northstar/messages`, {
      data: {
        tenant_id: 'default',
        channel: 'web',
        channel_user_id: `playwright-omnichannel-${Date.now()}`,
        customer_id: 'cust_1001',
        text: 'Add an espresso machine to my basket',
      },
      timeout: 45000,
    });
    expect(webResponse.ok(), `Northstar cart message returned HTTP ${webResponse.status()}`).toBeTruthy();
    const webBody = await webResponse.json();
    expect(webBody.status).toBe('success');
    expect(webBody.intent.intent).toBe('cart_management');

    const afterWeb = await getActiveCart(request);
    expect(afterWeb?.cart?.source).toBe('spree');
    expect(afterWeb?.cart?.cart_id, 'Web journey should create or reuse a live Spree cart').toBeTruthy();

    const whatsappResponse = await request.post(`${OPS_BASE}/api/v1/connectors/whatsapp/webhook`, {
      data: {
        entry: [{
          changes: [{
            value: {
              contacts: [{ wa_id: '447700900001', profile: { name: 'Ava Morgan' } }],
              messages: [{
                id: `wamid-proof-${Date.now()}`,
                from: '447700900001',
                timestamp: `${Math.floor(Date.now() / 1000)}`,
                type: 'text',
                text: { body: 'Add another espresso machine to my basket' },
              }],
            },
          }],
        }],
      },
      timeout: 45000,
    });
    expect(whatsappResponse.ok(), `WhatsApp webhook returned HTTP ${whatsappResponse.status()}`).toBeTruthy();
    const whatsappBody = await whatsappResponse.json();
    const processed = whatsappBody.processed?.[0];
    expect(processed?.status).toBe('dispatched');
    expect(processed?.route?.id).toBe('cart_management');

    const afterWhatsApp = await getActiveCart(request);
    expect(afterWhatsApp?.cart?.cart_id).toBe(afterWeb?.cart?.cart_id);
    expect(afterWhatsApp?.cart?.item_count).toBe((afterWeb?.cart?.item_count || 0) + 1);
    expect(afterWhatsApp?.cart?.items?.[0]?.name || '').toContain('Espresso');

    await test.info().attach('omnichannel-cart-proof.json', {
      body: JSON.stringify({
        before,
        web: {
          response_text: webBody.response_text,
          toolNames: findValues(webBody, 'tool_name'),
          sources: [...new Set(findValues(webBody, 'source'))].sort(),
        },
        whatsapp: processed,
        afterWeb,
        afterWhatsApp,
      }, null, 2),
      contentType: 'application/json',
    });
  });

  test('records the shopper-facing mixed-intent ACOS demo for investors', async ({ page }) => {
    await page.goto(`${OPS_BASE}/demo/agentic-shopper`);

    await expect(page.getByRole('heading', { name: /Conversation in\. ACOS orchestrates\. Commerce outcome out\./i })).toBeVisible();
    await expect(page.getByText('Live Spree Product')).toBeVisible({ timeout: 45000 });
    await expect(page.getByText('Last Week Order Fixture')).toBeVisible({ timeout: 45000 });
    await expect(page.locator('#product-card')).toContainText('Oxford Shirt');

    await page.screenshot({ path: `${OUTPUT_DIR}/05-shopper-demo-start.png`, fullPage: true });

    await page.getByRole('button', { name: 'Reset Demo State' }).click();
    await expect(page.locator('#summary-card')).toContainText('Demo state cleared', { timeout: 30000 });

    await page.getByRole('button', { name: 'Send Shopper Request' }).click();

    await expect(page.locator('#event-feed')).toContainText('commerce.checkout.completed', { timeout: 60000 });
    await expect(page.locator('#tool-feed')).toContainText('payments.create', { timeout: 60000 });
    await expect(page.locator('#execution-stage-card')).toContainText('Verified', { timeout: 60000 });
    await expect(page.locator('#run-status')).toContainText('Verified', { timeout: 60000 });
    await expect(page.locator('#summary-card')).toContainText('combined purchase and order-history request', { timeout: 60000 });
    await expect(page.locator('#checkout-order-card')).toContainText('New Checkout', { timeout: 60000 });
    await expect(page.locator('#checkout-order-card')).toContainText('Oxford Shirt', { timeout: 60000 });
    await expect(page.locator('#control-plane-card')).toContainText('Northstar mixed commerce orchestration', { timeout: 60000 });
    await expect(page.locator('#control-plane-card')).toContainText('Replay', { timeout: 60000 });
    await expect(page.locator('#control-plane-card')).toContainText('Order Agent', { timeout: 60000 });
    await expect(page.locator('#transaction-card')).toContainText('Payment', { timeout: 60000 });
    await expect(page.locator('#transaction-card')).toContainText('Spree Webhook', { timeout: 60000 });
    await expect(page.locator('#spree-surface-card')).toContainText('store_api_admin_portal_webhooks', { timeout: 60000 });
    await expect(page.locator('#spree-surface-card')).toContainText('production', { timeout: 60000 });
    await expect(page.locator('#spree-surface-card')).toContainText('127.0.0.1:3000/admin/orders', { timeout: 60000 });
    await expect(page.locator('#spree-surface-card')).toContainText('order.completed', { timeout: 60000 });
    await expect(page.locator('#trace-grid')).toContainText('Completed live checkout', { timeout: 60000 });
    await expect(page.locator('#trace-grid')).toContainText('Retrieved prior order', { timeout: 60000 });
    await expect(page.locator('#trace-grid')).toContainText('Created Check payment for $84.99.', { timeout: 60000 });
    await expect(page.locator('#messages')).toContainText('last week', { timeout: 60000 });

    await page.screenshot({ path: `${OUTPUT_DIR}/06-shopper-demo-verified.png`, fullPage: true });
  });

  test('presents the same shopper flow in a cleaner investor view', async ({ page }) => {
    await page.goto(`${OPS_BASE}/demo/agentic-shopper?view=investor`);

    await expect(page.getByRole('link', { name: 'Investor View' })).toHaveClass(/active/);
    await expect(page.locator('#investor-request-card')).toBeVisible();
    await expect(page.locator('#investor-actions-card')).toBeVisible();
    await expect(page.locator('#investor-result-card')).toBeVisible();
    await expect(page.locator('#investor-trust-card')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Live System Execution' })).toHaveCount(0);

    await page.screenshot({ path: `${OUTPUT_DIR}/07-shopper-investor-start.png`, fullPage: true });

    await page.getByRole('button', { name: 'Reset Demo State' }).click();
    await page.getByRole('button', { name: 'Send Shopper Request' }).click();

    await expect(page.locator('#investor-actions-card')).toContainText('mixed_order_purchase', { timeout: 60000 });
    await expect(page.locator('#investor-actions-card')).toContainText('Order Agent', { timeout: 60000 });
    await expect(page.locator('#investor-result-card')).toContainText('Oxford Shirt', { timeout: 60000 });
    await expect(page.locator('#investor-result-card')).toContainText('R', { timeout: 60000 });
    await expect(page.locator('#investor-trust-card')).toContainText('order.completed', { timeout: 60000 });
    await expect(page.locator('#investor-proof-log')).toContainText('Completed live checkout', { timeout: 60000 });
    await expect(page.locator('#messages')).toContainText('last week', { timeout: 60000 });

    await page.screenshot({ path: `${OUTPUT_DIR}/08-shopper-investor-verified.png`, fullPage: true });
  });

  test('records an investor-ready browser proof of the end-to-end flow', async ({ page }) => {
    await page.goto(`${OPS_BASE}/demo/investor-proof`);

    await expect(page.getByRole('heading', { name: /One agentic commerce layer/i })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Run Live Investor Proof' })).toBeVisible();

    await page.screenshot({ path: `${OUTPUT_DIR}/03-investor-proof-start.png`, fullPage: true });

    await page.getByRole('button', { name: 'Run Live Investor Proof' }).click();

    await expect(page.getByRole('heading', { name: 'Verified' })).toBeVisible({ timeout: 60000 });
    await expect(page.locator('#cart-summary')).toContainText('spree');
    await expect(page.locator('#cart-summary')).toContainText('Automatic Espresso Machine');
    await expect(page.locator('#responses')).toContainText('whatsapp_status');

    await page.screenshot({ path: `${OUTPUT_DIR}/04-investor-proof-verified.png`, fullPage: true });
  });
});

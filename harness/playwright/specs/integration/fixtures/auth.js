import { SignJWT } from 'jose';

/** Generate a signed HS256 JWT for Ops API calls. */
async function makeOpsToken() {
  const secret = new TextEncoder().encode(
    process.env.OPS_JWT_SECRET || 'dev-secret-key-for-testing-only'
  );
  return new SignJWT({ sub: 'e2e-test-user', role: 'admin' })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('1h')
    .sign(secret);
}

/**
 * Playwright fixture factory.
 * Use({ authHeaders, shopperHeaders }) in your test.
 *
 * authHeaders    — Authorization: Bearer <jwt>  for all Ops API calls.
 * shopperHeaders — X-API-Key: <key>             for all Shopper API calls.
 *
 * IMPORTANT: pass headers explicitly on every page.request call:
 *   await page.request.post(url, { headers: authHeaders, data: payload })
 */
export async function makeHeaders() {
  const token = await makeOpsToken();
  const authHeaders = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
  const shopperHeaders = {
    'X-API-Key': process.env.SHOPPER_API_KEY || 'test-key-1',
    'Content-Type': 'application/json',
  };
  return { authHeaders, shopperHeaders };
}

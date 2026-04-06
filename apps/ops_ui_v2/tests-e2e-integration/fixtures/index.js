import { test as base, expect } from '@playwright/test';
import { makeHeaders } from './auth.js';
import { makeDbFixture } from './db.js';

/**
 * Extended Playwright test with auth headers and DB access baked in.
 *
 * Each test receives:
 *   authHeaders    — { Authorization, Content-Type } for Ops API
 *   shopperHeaders — { X-API-Key, Content-Type } for Shopper API
 *   db             — { query(sql, params) } Postgres helper
 *
 * The DB pool is created once per worker and torn down after all tests in the file.
 * Auth headers are regenerated fresh for each test (token expiry: 1h).
 */

export const test = base.extend({
  // Auth headers — generated per test
  authHeaders: async ({}, use) => {
    const { authHeaders } = await makeHeaders();
    await use(authHeaders);
  },

  shopperHeaders: async ({}, use) => {
    const { shopperHeaders } = await makeHeaders();
    await use(shopperHeaders);
  },

  // DB — one pool per worker, properly torn down after all tests in the file.
  // scope:'worker' ensures Playwright closes the pool before the worker exits,
  // preventing the pg pool from keeping the Node.js event loop alive (hanging worker).
  db: [async ({}, use) => {
    const db = makeDbFixture();
    // Connectivity probe — fail fast with a clear message if DB is unreachable
    try {
      await db.query('SELECT 1');
    } catch {
      await db.end();
      throw new Error(
        'Postgres is not reachable. Is "docker compose up" running? Check DATABASE_URL env var.'
      );
    }
    await use(db);
    await db.end(); // always runs — even if tests throw
  }, { scope: 'worker' }],
});

export { expect };

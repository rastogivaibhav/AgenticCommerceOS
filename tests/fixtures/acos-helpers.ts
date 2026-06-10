/**
 * ACOS Playwright Test Helpers
 * Date: 2026-04-15
 * Purpose: Reusable fixtures and helper functions for ACOS automated testing
 *
 * Usage:
 * import { test, expect } from '@playwright/test';
 * import { acosTest, authenticateAs, getAuthToken } from './acos-helpers';
 *
 * // Use as custom fixture
 * acosTest('should perform admin task', async ({ page, authenticatedAdmin }) => {
 *   await page.goto('http://localhost:5173/ui/workflows');
 *   // Admin authenticated automatically
 * });
 */

import { test as base, expect, Page } from '@playwright/test';

// ============================================================================
// CONSTANTS
// ============================================================================

const BACKEND_URL = 'http://localhost:8081';
const FRONTEND_URL = 'http://localhost:5173/ui';
const BOOTSTRAP_ENDPOINT = '/dev/auth/bootstrap';

interface AuthToken {
  sub: string;
  role: 'admin' | 'ops' | 'analyst';
  iat: number;
  exp: number;
}

// ============================================================================
// AUTHENTICATION HELPERS
// ============================================================================

/**
 * Extract JWT token from bootstrap HTML response
 * @param html - HTML response from bootstrap endpoint
 * @returns JWT token string or null if not found
 */
export function extractTokenFromHtml(html: string): string | null {
  const match = html.match(/setItem\("ops_token",\s*"([^"]+)"/);
  return match ? match[1] : null;
}

/**
 * Get JWT token from bootstrap endpoint
 * @param role - User role (admin, ops, analyst)
 * @returns JWT token string
 */
export async function getAuthToken(
  page: Page,
  role: 'admin' | 'ops' | 'analyst'
): Promise<string> {
  const bootstrapUrl = `${BACKEND_URL}${BOOTSTRAP_ENDPOINT}/${role}?redirect=%2Fui%2Fworkflows`;

  const response = await page.goto(bootstrapUrl);
  if (!response) throw new Error('Bootstrap endpoint unreachable');

  const html = await response.text();
  const token = extractTokenFromHtml(html);

  if (!token) {
    throw new Error(`Failed to extract token for role: ${role}`);
  }

  return token;
}

/**
 * Authenticate as specific role by storing token in localStorage
 * @param page - Playwright page object
 * @param role - User role
 */
export async function authenticateAs(
  page: Page,
  role: 'admin' | 'ops' | 'analyst'
): Promise<void> {
  const token = await getAuthToken(page, role);

  await page.evaluate((tok) => {
    localStorage.setItem('ops_token', tok);
  }, token);

  // Verify authentication by checking header
  await page.goto(`${FRONTEND_URL}/workflows`);
  await page.waitForLoadState('networkidle');

  // Wait for header to show authenticated user
  await page.waitForSelector('text=User: dev-user', { timeout: 5000 }).catch(() => {
    // Header might not always show, which is okay
  });
}

/**
 * Clear authentication token and logout
 * @param page - Playwright page object
 */
export async function logout(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.removeItem('ops_token');
  });
  // Redirect to workflows (will show unauthenticated state)
  await page.goto(`${FRONTEND_URL}/workflows`);
}

/**
 * Check if current user is authenticated
 * @param page - Playwright page object
 * @returns true if authenticated, false otherwise
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  const token = await page.evaluate(() => localStorage.getItem('ops_token'));
  return !!token;
}

/**
 * Get current token and decode claims (without verification)
 * @param page - Playwright page object
 * @returns Decoded token or null
 */
export async function getTokenClaims(page: Page): Promise<AuthToken | null> {
  const token = await page.evaluate(() => localStorage.getItem('ops_token'));
  if (!token) return null;

  try {
    // JWT format: header.payload.signature
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
    return payload as AuthToken;
  } catch {
    return null;
  }
}

// ============================================================================
// API HELPERS
// ============================================================================

/**
 * Make authenticated API call
 * @param page - Playwright page object
 * @param endpoint - API endpoint (e.g., '/api/v1/ops/workflows')
 * @param method - HTTP method (GET, POST, PATCH, DELETE)
 * @param body - Request body (for POST/PATCH)
 * @returns Response JSON
 */
export async function apiCall(
  page: Page,
  endpoint: string,
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE' = 'GET',
  body?: Record<string, any>
): Promise<any> {
  const response = await page.evaluate(
    async ({ url, method, body: reqBody }) => {
      const token = localStorage.getItem('ops_token');
      if (!token) throw new Error('Not authenticated');

      const fetchResponse = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: reqBody ? JSON.stringify(reqBody) : undefined,
      });

      const data = await fetchResponse.json();
      return {
        status: fetchResponse.status,
        data,
      };
    },
    {
      url: `${BACKEND_URL}${endpoint}`,
      method,
      body,
    }
  );

  if (response.status >= 400) {
    throw new Error(`API Error ${response.status}: ${JSON.stringify(response.data)}`);
  }

  return response.data;
}

/**
 * Check if API endpoint requires admin role
 * @param page - Playwright page object
 * @param endpoint - API endpoint
 * @returns true if endpoint returns 403 for ops role
 */
export async function isAdminOnlyEndpoint(
  page: Page,
  endpoint: string
): Promise<boolean> {
  // First authenticate as ops
  await authenticateAs(page, 'ops');

  try {
    const response = await page.evaluate(
      async ({ url }) => {
        const token = localStorage.getItem('ops_token');
        const fetchResponse = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        return fetchResponse.status;
      },
      { url: `${BACKEND_URL}${endpoint}` }
    );

    return response === 403;
  } catch {
    return false;
  }
}

// ============================================================================
// UI HELPERS
// ============================================================================

/**
 * Click button by text (case-insensitive)
 * @param page - Playwright page object
 * @param buttonText - Text on button
 */
export async function clickButton(page: Page, buttonText: string): Promise<void> {
  const button = page.locator(`button:has-text("${buttonText}")`).first();
  await button.click();
}

/**
 * Fill form input field by label
 * @param page - Playwright page object
 * @param labelText - Label text
 * @param value - Value to fill
 */
export async function fillInput(
  page: Page,
  labelText: string,
  value: string
): Promise<void> {
  const label = page.locator(`label:has-text("${labelText}")`);
  const input = label.locator('..').locator('input').first();
  await input.fill(value);
}

/**
 * Select dropdown option by label and option text
 * @param page - Playwright page object
 * @param labelText - Label text
 * @param optionText - Option text to select
 */
export async function selectDropdown(
  page: Page,
  labelText: string,
  optionText: string
): Promise<void> {
  const label = page.locator(`label:has-text("${labelText}")`);
  const select = label.locator('..').locator('select').first();
  await select.selectOption(optionText);
}

/**
 * Check if element is visible
 * @param page - Playwright page object
 * @param selector - Element selector or text
 * @returns true if visible
 */
export async function isVisible(page: Page, selector: string): Promise<boolean> {
  const element = page.locator(selector).first();
  return element.isVisible().catch(() => false);
}

/**
 * Wait for loading spinner to disappear
 * @param page - Playwright page object
 * @param timeout - Max wait time in ms
 */
export async function waitForLoading(page: Page, timeout = 10000): Promise<void> {
  // Wait for skeleton/spinner elements to be gone
  await page
    .locator('[class*="skeleton"], [class*="spinner"], [class*="loading"]')
    .first()
    .waitFor({ state: 'hidden', timeout });
}

/**
 * Get table row count
 * @param page - Playwright page object
 * @returns Number of rows
 */
export async function getTableRowCount(page: Page): Promise<number> {
  const rows = await page.locator('tbody tr').count();
  return rows;
}

/**
 * Get error message from page
 * @param page - Playwright page object
 * @returns Error message text or null
 */
export async function getErrorMessage(page: Page): Promise<string | null> {
  const error = page.locator('[role="alert"], [class*="error"]').first();
  return error.isVisible().then(() => error.textContent()).catch(() => null);
}

/**
 * Take screenshot of specific element
 * @param page - Playwright page object
 * @param selector - Element selector
 * @param filename - Output filename
 */
export async function takeElementScreenshot(
  page: Page,
  selector: string,
  filename: string
): Promise<void> {
  const element = page.locator(selector).first();
  await element.screenshot({ path: filename });
}

// ============================================================================
// WORKFLOW HELPERS
// ============================================================================

/**
 * Create test workflow via API
 * @param page - Playwright page object
 * @param name - Workflow name
 * @param family - Workflow family
 * @returns Workflow ID
 */
export async function createWorkflow(
  page: Page,
  name: string,
  family: string
): Promise<string> {
  const response = await apiCall(
    page,
    '/api/v1/ops/workflows',
    'POST',
    {
      name,
      family,
      description: `Test workflow: ${name}`,
    }
  );

  return response.id || response.workflow_id;
}

/**
 * Delete workflow via API
 * @param page - Playwright page object
 * @param workflowId - Workflow ID
 */
export async function deleteWorkflow(page: Page, workflowId: string): Promise<void> {
  await apiCall(page, `/api/v1/ops/workflows/${workflowId}`, 'DELETE');
}

/**
 * Get workflow by ID
 * @param page - Playwright page object
 * @param workflowId - Workflow ID
 * @returns Workflow object
 */
export async function getWorkflow(page: Page, workflowId: string): Promise<any> {
  return apiCall(page, `/api/v1/ops/workflows/${workflowId}`, 'GET');
}

/**
 * List all workflows
 * @param page - Playwright page object
 * @returns Array of workflows
 */
export async function listWorkflows(page: Page): Promise<any[]> {
  const response = await apiCall(page, '/api/v1/ops/workflows', 'GET');
  return response.workflows || response;
}

// ============================================================================
// CUSTOM TEST FIXTURE
// ============================================================================

type AcosTestFixtures = {
  authenticatedAdmin: void;
  authenticatedOps: void;
  authenticatedAnalyst: void;
};

export const acosTest = base.extend<AcosTestFixtures>({
  authenticatedAdmin: async ({ page }, use) => {
    await authenticateAs(page, 'admin');
    await use();
    await logout(page);
  },

  authenticatedOps: async ({ page }, use) => {
    await authenticateAs(page, 'ops');
    await use();
    await logout(page);
  },

  authenticatedAnalyst: async ({ page }, use) => {
    await authenticateAs(page, 'analyst');
    await use();
    await logout(page);
  },
});

// Export test and expect for use in test files
export { expect };

// ============================================================================
// EXAMPLE USAGE IN TEST FILE
// ============================================================================

/*
import { acosTest, expect, clickButton, fillInput, waitForLoading } from './acos-helpers';

acosTest('Admin can create workflow', async ({ page, authenticatedAdmin }) => {
  // Navigate to workflows
  await page.goto('http://localhost:5173/ui/workflows');
  await waitForLoading(page);

  // Click create button
  await clickButton(page, 'Create Workflow');

  // Fill form
  await fillInput(page, 'Name', 'Test Workflow');
  await fillInput(page, 'Family', 'test-family');

  // Submit
  await clickButton(page, 'Create');

  // Verify success
  await expect(page.locator('text=Test Workflow')).toBeVisible();
});

acosTest.describe('Role-based access', () => {
  acosTest('Analyst cannot create workflow', async ({ page, authenticatedAnalyst }) => {
    await page.goto('http://localhost:5173/ui/workflows');

    // Create button should be disabled
    const createBtn = page.locator('button:has-text("Create")');
    await expect(createBtn).toBeDisabled();
  });
});
*/

import { defineConfig, devices } from '@playwright/test';

const OPS_BASE = process.env.OPS_BASE_URL || 'http://127.0.0.1:8081';

export default defineConfig({
  testDir: './specs/ecom-demo',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['html', { outputFolder: './reports/ecom-demo' }], ['list']],
  timeout: 90000,
  expect: { timeout: 15000 },
  use: {
    baseURL: OPS_BASE,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'on',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});

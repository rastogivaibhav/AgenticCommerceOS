import { test, expect } from '@playwright/test';

test.describe('Ops Dashboard V2', () => {
  test('loads the primary list view and navigates successfully', async ({ page }) => {
    // Navigate to the base URL
    await page.goto('/');

    // Verify the navbar loads
    await expect(page.locator('.sidebar-links')).toBeVisible();
    await expect(page.getByText('ACOS', { exact: true })).toBeVisible();

    // Verify Agents page is the default root
    await expect(page.getByRole('heading', { name: 'System Agents' })).toBeVisible();

    // Click on the Simulation nav item
    await page.getByText('Simulation').click();

    // Verify user is taken to the simulation view
    await expect(page.getByText('Journey Planner & Simulation')).toBeVisible();
    
    // Switch to Skills view
    await page.getByText('Skills').click();
    await expect(page.getByRole('heading', { name: 'Skill Library' })).toBeVisible();
  });
});

import { test, expect } from '@playwright/test';

test.describe('Ops Dashboard V2 - Simulation Graph', () => {
  test('interacts with the React Flow canvas', async ({ page }) => {
    // Navigate and go to Simulations tab
    await page.goto('/');
    await page.getByText('Simulation').click();

    // Make sure we are in builder mode first
    await expect(page.getByText('Journey Planner & Simulation')).toBeVisible();
    
    // Check that default toolbox renders
    await expect(page.getByText('Drag Agents')).toBeVisible();
    await expect(page.getByText('Returns Bot')).toBeVisible();

    // Toggle Live Traffic via the switch
    await page.getByText('Live Traffic').click();

    // Check Live execution banner appears and toolbox disappears
    await expect(page.getByText('Live execution traffic flowing...')).toBeVisible();
    await expect(page.getByText('Drag Agents')).not.toBeVisible();
  });
});

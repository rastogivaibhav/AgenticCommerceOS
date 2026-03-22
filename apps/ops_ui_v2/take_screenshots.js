import { chromium } from '@playwright/test';
import * as path from 'path';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const artifactDir = 'C:\\Users\\vrast\\.gemini\\antigravity\\brain\\0b68a908-ed73-446b-bc05-92d7612de6cb';

  await page.goto('http://localhost:5173/ui/');
  
  // 1. Agents Page
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(artifactDir, 'agents_view.png') });
  
  // 1b. Agents Form Open
  await page.getByText('Campaign Manager', { exact: true }).click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(artifactDir, 'agents_editor.png') });
  await page.getByText('×').click();

  // 2. Skills Page
  await page.getByText('Skills').click();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(artifactDir, 'skills_view.png') });

  // 2b. Skills Form Open
  await page.getByText('Process Refund', { exact: true }).click();
  await page.waitForTimeout(1500); // Wait for monaco
  await page.screenshot({ path: path.join(artifactDir, 'skills_editor.png') });

  // 3. Simulations Page
  await page.getByText('Simulation').click();
  await page.waitForTimeout(1500); // Wait for react flow nodes to draw
  await page.screenshot({ path: path.join(artifactDir, 'simulation_builder.png') });

  // 3b. Simulations Live Traffic
  await page.getByText('Live Traffic').click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(artifactDir, 'simulation_live.png') });

  await browser.close();
  console.log('Screenshots generated successfully.');
})();

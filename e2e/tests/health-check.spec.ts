import { test, expect } from '@playwright/test';

test.describe('Health Check Tests', () => {
  test('backend health endpoint should be accessible', async ({ page }) => {
    const response = await page.goto('http://localhost:8000/health');
    expect(response?.status()).toBe(200);
  });

  test('frontend should load successfully', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check that the page title is set
    await expect(page).toHaveTitle(/WellnessWay/);
    
    // Check that the main content is visible
    const mainContent = page.locator('main, #root, [data-testid="app"]').first();
    await expect(mainContent).toBeVisible();
  });

  test('API documentation should be accessible', async ({ page }) => {
    const response = await page.goto('http://localhost:8000/docs');
    expect(response?.status()).toBe(200);
    
    // Check that Swagger UI loads
    await page.waitForSelector('.swagger-ui');
    const swaggerUI = page.locator('.swagger-ui');
    await expect(swaggerUI).toBeVisible();
  });

  test('frontend should handle API connection', async ({ page }) => {
    await page.goto('/');
    
    // Wait for any initial API calls to complete
    await page.waitForLoadState('networkidle');
    
    // Check that there are no console errors related to API connectivity
    const logs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        logs.push(msg.text());
      }
    });
    
    // Trigger a page interaction that might make API calls
    await page.waitForTimeout(2000);
    
    // Filter out non-API related errors
    const apiErrors = logs.filter(log => 
      log.includes('fetch') || 
      log.includes('network') || 
      log.includes('8000') ||
      log.includes('API')
    );
    
    expect(apiErrors.length).toBe(0);
  });
});
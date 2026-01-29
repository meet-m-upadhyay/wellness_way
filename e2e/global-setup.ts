import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('Starting global setup...');
  
  // Wait for services to be ready
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Wait for backend to be ready
  let backendReady = false;
  let attempts = 0;
  const maxAttempts = 30;
  
  while (!backendReady && attempts < maxAttempts) {
    try {
      const response = await page.goto('http://localhost:8000/health');
      if (response && response.ok()) {
        backendReady = true;
        console.log('Backend is ready');
      }
    } catch (error) {
      console.log(`Waiting for backend... (attempt ${attempts + 1}/${maxAttempts})`);
      await page.waitForTimeout(2000);
      attempts++;
    }
  }
  
  if (!backendReady) {
    throw new Error('Backend failed to start within timeout period');
  }
  
  // Wait for frontend to be ready
  let frontendReady = false;
  attempts = 0;
  
  while (!frontendReady && attempts < maxAttempts) {
    try {
      const response = await page.goto('http://localhost:3000');
      if (response && response.ok()) {
        frontendReady = true;
        console.log('Frontend is ready');
      }
    } catch (error) {
      console.log(`Waiting for frontend... (attempt ${attempts + 1}/${maxAttempts})`);
      await page.waitForTimeout(2000);
      attempts++;
    }
  }
  
  if (!frontendReady) {
    throw new Error('Frontend failed to start within timeout period');
  }
  
  await browser.close();
  console.log('Global setup completed');
}

export default globalSetup;
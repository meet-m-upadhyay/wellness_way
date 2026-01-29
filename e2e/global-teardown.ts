import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('Starting global teardown...');
  
  // Add any cleanup logic here
  // For example, cleaning up test data, stopping services, etc.
  
  console.log('Global teardown completed');
}

export default globalTeardown;
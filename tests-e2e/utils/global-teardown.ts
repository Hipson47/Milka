import { FullConfig } from '@playwright/test';

/**
 * Global teardown for Playwright tests
 */
async function globalTeardown(config: FullConfig) {
  console.log('Starting global teardown for E2E tests...');
  
  // Cleanup operations if needed
  // For now, just log completion
  
  console.log('Global teardown completed');
}

export default globalTeardown;

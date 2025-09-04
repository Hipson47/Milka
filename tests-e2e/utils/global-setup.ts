import { FullConfig } from '@playwright/test';

/**
 * Global setup for Playwright tests
 */
async function globalSetup(config: FullConfig) {
  console.log('Starting global setup for E2E tests...');
  
  // Check if backend is available
  const backendUrl = process.env.E2E_API_URL || 'http://localhost:8000';
  
  try {
    const response = await fetch(`${backendUrl}/api/health`);
    if (!response.ok) {
      throw new Error(`Backend health check failed: ${response.status}`);
    }
    console.log('✓ Backend is healthy');
  } catch (error) {
    console.warn('⚠ Backend not available, tests may fail:', error);
  }
  
  // Create test fixtures if they don't exist
  await createTestFixtures();
  
  console.log('Global setup completed');
}

async function createTestFixtures() {
  const fs = require('fs');
  const path = require('path');
  const { createCanvas } = require('canvas');
  
  const fixturesDir = path.join(__dirname, '../fixtures');
  
  // Create fixtures directory if it doesn't exist
  if (!fs.existsSync(fixturesDir)) {
    fs.mkdirSync(fixturesDir, { recursive: true });
  }
  
  // Create test image (512x512 PNG)
  const testImagePath = path.join(fixturesDir, 'test-image.png');
  if (!fs.existsSync(testImagePath)) {
    console.log('Creating test image fixture...');
    
    const canvas = createCanvas(512, 512);
    const ctx = canvas.getContext('2d');
    
    // Create a gradient background
    const gradient = ctx.createLinearGradient(0, 0, 512, 512);
    gradient.addColorStop(0, '#ff7f50');
    gradient.addColorStop(1, '#6a5acd');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 512, 512);
    
    // Add some geometric shapes
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(100, 100, 100, 100);
    
    ctx.fillStyle = '#000000';
    ctx.beginPath();
    ctx.arc(350, 150, 50, 0, 2 * Math.PI);
    ctx.fill();
    
    // Save as PNG
    const buffer = canvas.toBuffer('image/png');
    fs.writeFileSync(testImagePath, buffer);
    console.log('✓ Test image created');
  }
  
  // Create test mask (512x512 PNG with alpha)
  const testMaskPath = path.join(fixturesDir, 'test-mask.png');
  if (!fs.existsSync(testMaskPath)) {
    console.log('Creating test mask fixture...');
    
    const canvas = createCanvas(512, 512);
    const ctx = canvas.getContext('2d');
    
    // Transparent background
    ctx.clearRect(0, 0, 512, 512);
    
    // White circle in center (area to inpaint)
    ctx.fillStyle = 'rgba(255, 255, 255, 255)';
    ctx.beginPath();
    ctx.arc(256, 256, 80, 0, 2 * Math.PI);
    ctx.fill();
    
    // Save as PNG with alpha
    const buffer = canvas.toBuffer('image/png');
    fs.writeFileSync(testMaskPath, buffer);
    console.log('✓ Test mask created');
  }
}

export default globalSetup;

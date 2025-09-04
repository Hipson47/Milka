import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * E2E tests for the image inpainting workflow
 */
test.describe('Image Inpainting Workflow', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for the page to load
    await expect(page.locator('h1')).toContainText('NanoBanana Inpainting');
    
    // Check that all main sections are visible
    await expect(page.locator('text=1. Upload Image')).toBeVisible();
    await expect(page.locator('text=2. Draw Mask')).toBeVisible();
    await expect(page.locator('text=3. Enter Prompt')).toBeVisible();
    await expect(page.locator('text=4. Advanced Settings')).toBeVisible();
  });

  test('should complete full inpainting workflow', async ({ page }) => {
    // Step 1: Upload an image
    const imageUpload = page.locator('input[type="file"]').first();
    const imagePath = path.join(__dirname, '../fixtures/test-image.png');
    await imageUpload.setInputFiles(imagePath);
    
    // Verify image preview appears
    await expect(page.locator('img[alt="Uploaded image"]')).toBeVisible();
    
    // Step 2: Draw on mask canvas
    const canvas = page.locator('canvas').last(); // Mask canvas should be the last one
    await expect(canvas).toBeVisible();
    
    // Click draw mode button (should be selected by default)
    await page.locator('button:has-text("🖌️ Draw")').click();
    
    // Draw on canvas - simulate drawing a mask
    const canvasBox = await canvas.boundingBox();
    if (canvasBox) {
      // Draw a circle in the center
      const centerX = canvasBox.x + canvasBox.width / 2;
      const centerY = canvasBox.y + canvasBox.height / 2;
      
      await page.mouse.move(centerX - 20, centerY - 20);
      await page.mouse.down();
      await page.mouse.move(centerX + 20, centerY - 20);
      await page.mouse.move(centerX + 20, centerY + 20);
      await page.mouse.move(centerX - 20, centerY + 20);
      await page.mouse.move(centerX - 20, centerY - 20);
      await page.mouse.up();
    }
    
    // Step 3: Enter a prompt
    const promptTextarea = page.locator('textarea[placeholder*="Describe what you want"]');
    await promptTextarea.fill('A beautiful red rose in full bloom');
    
    // Verify character counter
    await expect(page.locator('text=37/500')).toBeVisible();
    
    // Step 4: Adjust advanced settings (optional)
    const strengthSlider = page.locator('input[type="range"]').first();
    await strengthSlider.fill('0.7');
    
    // Step 5: Submit the inpainting request
    const generateButton = page.locator('button:has-text("🎨 Generate Inpainting")');
    await expect(generateButton).toBeEnabled();
    await generateButton.click();
    
    // Verify loading state
    await expect(page.locator('text=Processing...')).toBeVisible();
    await expect(generateButton).toBeDisabled();
    
    // Wait for result (this might take a while in real scenarios)
    await expect(page.locator('text=Processing...')).not.toBeVisible({ timeout: 60000 });
    
    // Verify result is displayed
    await expect(page.locator('text=Inpainted Result')).toBeVisible();
    await expect(page.locator('img[alt="Inpainted result"]')).toBeVisible();
    
    // Verify download button is available
    await expect(page.locator('button:has-text("📥 Download Result")')).toBeVisible();
    
    // Test download functionality
    const downloadPromise = page.waitForEvent('download');
    await page.locator('button:has-text("📥 Download Result")').click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe('inpainted-image.png');
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit without any inputs
    const generateButton = page.locator('button:has-text("🎨 Generate Inpainting")');
    await expect(generateButton).toBeDisabled();
    
    // Upload image only
    const imageUpload = page.locator('input[type="file"]').first();
    const imagePath = path.join(__dirname, '../fixtures/test-image.png');
    await imageUpload.setInputFiles(imagePath);
    
    // Still should be disabled (no mask or prompt)
    await expect(generateButton).toBeDisabled();
    
    // Add prompt but no mask
    const promptTextarea = page.locator('textarea[placeholder*="Describe what you want"]');
    await promptTextarea.fill('A test prompt');
    
    // Still should be disabled (no mask)
    await expect(generateButton).toBeDisabled();
    
    // Draw mask
    const canvas = page.locator('canvas').last();
    const canvasBox = await canvas.boundingBox();
    if (canvasBox) {
      await page.mouse.move(canvasBox.x + 100, canvasBox.y + 100);
      await page.mouse.down();
      await page.mouse.move(canvasBox.x + 200, canvasBox.y + 200);
      await page.mouse.up();
    }
    
    // Now should be enabled
    await expect(generateButton).toBeEnabled();
  });

  test('should handle canvas drawing tools', async ({ page }) => {
    // Upload image first
    const imageUpload = page.locator('input[type="file"]').first();
    const imagePath = path.join(__dirname, '../fixtures/test-image.png');
    await imageUpload.setInputFiles(imagePath);
    
    await expect(page.locator('img[alt="Uploaded image"]')).toBeVisible();
    
    // Test draw mode
    const drawButton = page.locator('button:has-text("🖌️ Draw")');
    const eraseButton = page.locator('button:has-text("🧽 Erase")');
    const clearButton = page.locator('button:has-text("🗑️ Clear")');
    const undoButton = page.locator('button:has-text("↶ Undo")');
    
    // Draw mode should be selected by default
    await expect(drawButton).toHaveClass(/btn-primary/);
    
    // Switch to erase mode
    await eraseButton.click();
    await expect(eraseButton).toHaveClass(/btn-primary/);
    await expect(drawButton).not.toHaveClass(/btn-primary/);
    
    // Test brush size control
    const brushSlider = page.locator('input[type="range"]:has(~ span)');
    await brushSlider.fill('30');
    await expect(page.locator('text=30')).toBeVisible();
    
    // Draw something
    const canvas = page.locator('canvas').last();
    const canvasBox = await canvas.boundingBox();
    if (canvasBox) {
      await page.mouse.move(canvasBox.x + 50, canvasBox.y + 50);
      await page.mouse.down();
      await page.mouse.move(canvasBox.x + 150, canvasBox.y + 150);
      await page.mouse.up();
    }
    
    // Test undo (should be enabled after drawing)
    await expect(undoButton).not.toBeDisabled();
    await undoButton.click();
    
    // Test clear
    await clearButton.click();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('**/api/edit', (route) => {
      route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error_message: 'Invalid image format',
          error_code: 'HTTP_422'
        })
      });
    });
    
    // Complete the workflow
    const imageUpload = page.locator('input[type="file"]').first();
    const imagePath = path.join(__dirname, '../fixtures/test-image.png');
    await imageUpload.setInputFiles(imagePath);
    
    // Draw mask
    const canvas = page.locator('canvas').last();
    const canvasBox = await canvas.boundingBox();
    if (canvasBox) {
      await page.mouse.move(canvasBox.x + 100, canvasBox.y + 100);
      await page.mouse.down();
      await page.mouse.move(canvasBox.x + 200, canvasBox.y + 200);
      await page.mouse.up();
    }
    
    // Add prompt
    const promptTextarea = page.locator('textarea[placeholder*="Describe what you want"]');
    await promptTextarea.fill('Test prompt');
    
    // Submit
    const generateButton = page.locator('button:has-text("🎨 Generate Inpainting")');
    await generateButton.click();
    
    // Verify error is displayed
    await expect(page.locator('text=Error:')).toBeVisible();
    await expect(page.locator('text=Invalid image format')).toBeVisible();
    
    // Verify button is re-enabled
    await expect(generateButton).toBeEnabled();
  });

  test('should be responsive on mobile devices', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip('This test only runs on mobile viewports');
    }
    
    // Check that the layout adapts to mobile
    await expect(page.locator('.grid')).toBeVisible();
    
    // Check that touch interactions work on canvas
    const canvas = page.locator('canvas').last();
    
    // Upload image first
    const imageUpload = page.locator('input[type="file"]').first();
    const imagePath = path.join(__dirname, '../fixtures/test-image.png');
    await imageUpload.setInputFiles(imagePath);
    
    await expect(canvas).toBeVisible();
    
    // Test touch drawing
    const canvasBox = await canvas.boundingBox();
    if (canvasBox) {
      await page.touchscreen.tap(canvasBox.x + 100, canvasBox.y + 100);
    }
    
    // Check that all controls are accessible
    await expect(page.locator('button:has-text("🖌️ Draw")')).toBeVisible();
    await expect(page.locator('button:has-text("🧽 Erase")')).toBeVisible();
  });

  test('should have accessible controls', async ({ page }) => {
    // Check for proper ARIA labels and keyboard navigation
    
    // File upload should be accessible
    const fileInput = page.locator('input[type="file"]').first();
    await expect(fileInput).toHaveAttribute('accept', /image/);
    
    // Canvas should have proper labeling
    const canvas = page.locator('canvas').last();
    
    // Upload image to enable canvas
    const imagePath = path.join(__dirname, '../fixtures/test-image.png');
    await fileInput.setInputFiles(imagePath);
    
    await expect(canvas).toBeVisible();
    
    // Control buttons should be keyboard accessible
    const drawButton = page.locator('button:has-text("🖌️ Draw")');
    await drawButton.focus();
    await expect(drawButton).toBeFocused();
    
    // Form controls should have proper labels
    const promptTextarea = page.locator('textarea[placeholder*="Describe what you want"]');
    await expect(promptTextarea).toBeVisible();
    
    const strengthSlider = page.locator('input[type="range"]').first();
    await expect(strengthSlider).toHaveAttribute('min');
    await expect(strengthSlider).toHaveAttribute('max');
  });
});

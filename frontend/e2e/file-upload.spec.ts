import { test, expect } from '@playwright/test';

test.describe('File Upload Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication for these tests
    await page.addInitScript(() => {
      // Mock next-auth session
      window.localStorage.setItem('next-auth.session-token', 'mock-token');
    });
  });

  test('should show file upload area', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load and check if upload area is visible
    await expect(page.getByText('ここにファイルをドラッグ＆ドロップするか')).toBeVisible();
    await expect(page.getByText('対応ファイル: .xlsx, .xls')).toBeVisible();
  });

  test('should show password input fields', async ({ page }) => {
    await page.goto('/');
    
    // Check password input fields
    await expect(page.getByPlaceholder('パスワード候補1')).toBeVisible();
    await expect(page.getByPlaceholder('パスワード候補2（任意）')).toBeVisible();
  });

  test('should show process button when files are selected', async ({ page }) => {
    await page.goto('/');
    
    // Initially, process button should be disabled
    const processButton = page.getByRole('button', { name: '解除開始' });
    await expect(processButton).toBeVisible();
    await expect(processButton).toBeDisabled();
  });

  test('should show clear button', async ({ page }) => {
    await page.goto('/');
    
    const clearButton = page.getByRole('button', { name: 'クリア' });
    await expect(clearButton).toBeVisible();
    await expect(clearButton).toBeEnabled();
  });

  test('should handle file input interaction', async ({ page }) => {
    await page.goto('/');
    
    // Click on the upload area
    const uploadArea = page.getByText('ここにファイルをドラッグ＆ドロップするか').locator('..');
    await uploadArea.click();
    
    // Check if file input exists (it's hidden but should be in DOM)
    const fileInput = page.locator('#fileInput');
    await expect(fileInput).toBeAttached();
    await expect(fileInput).toHaveAttribute('accept', '.xlsx, .xls');
    await expect(fileInput).toHaveAttribute('multiple');
  });
});
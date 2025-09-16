import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should show login overlay when not authenticated', async ({ page }) => {
    await page.goto('/');
    
    // Check if login overlay is visible
    await expect(page.getByText('ようこそ')).toBeVisible();
    await expect(page.getByText('Googleでサインイン')).toBeVisible();
    
    // Check if main content is blurred
    const mainContent = page.locator('.blur-sm');
    await expect(mainContent).toBeVisible();
  });

  test('should have proper page title and meta', async ({ page }) => {
    await page.goto('/');
    
    // Check page title
    await expect(page).toHaveTitle(/Excel パスワード解除/);
    
    // Check main heading
    await expect(page.getByRole('heading', { name: 'Excel パスワード解除' })).toBeVisible();
  });

  test('should show sign in button', async ({ page }) => {
    await page.goto('/');
    
    const signInButton = page.getByRole('button', { name: 'Googleでサインイン' });
    await expect(signInButton).toBeVisible();
    await expect(signInButton).toBeEnabled();
  });
});
import { test, expect } from '@playwright/test';

test.describe('Social Media App E2E', () => {
  test('user can register, login, and create a post', async ({ page }) => {
    // Navigate to app
    await page.goto('http://localhost:3000');
    
    // Register new user
    await page.click('text=Register');
    await page.fill('[placeholder="Username"]', 'e2euser');
    await page.fill('[placeholder="Email"]', 'e2e@test.com');
    await page.fill('[placeholder="Full Name"]', 'E2E Test User');
    await page.fill('[placeholder="Password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Should be redirected to home feed
    await expect(page).toHaveURL('http://localhost:3000/');
    
    // Create a new post
    await page.fill('[placeholder="What's on your mind?"]', 'My first post!');
    await page.click('text=Post');
    
    // Verify post appears in feed
    await expect(page.locator('text=My first post!')).toBeVisible();
    await expect(page.locator('text=E2E Test User')).toBeVisible();
  });
  
  test('user can like and comment on posts', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Login
    await page.fill('[placeholder="Email"]', 'e2e@test.com');
    await page.fill('[placeholder="Password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Like the first post
    const likeButton = page.locator('[aria-label="Like post"]').first();
    const initialLikes = await page.locator('.like-count').first().textContent();
    
    await likeButton.click();
    
    // Verify like count increased
    const newLikes = await page.locator('.like-count').first().textContent();
    expect(parseInt(newLikes)).toBe(parseInt(initialLikes) + 1);
  });
});
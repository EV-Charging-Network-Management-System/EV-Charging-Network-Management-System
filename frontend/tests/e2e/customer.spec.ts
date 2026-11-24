import { expect, test } from '@playwright/test';

test('a customer can sign in, view stations and sign out', async ({ page, request }) => {
  const email = `driver-${crypto.randomUUID()}@example.com`;
  const password = 'BrowserTest123!';
  const registered = await request.post('/api/v1/auth/register', {
    data: { full_name: 'Browser Test Driver', email, password },
  });
  expect(registered.status()).toBe(201);

  await page.goto('/login');
  await page.getByLabel('Email Address').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign In to Network' }).click();
  await expect(page).toHaveURL(/\/customer$/);

  await page.getByRole('link', { name: 'Stations', exact: true }).click();
  await expect(page).toHaveURL(/\/stations$/);
  await expect(page.getByText('GreenCharge Koramangala', { exact: true }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Sign out' }).click();
  await expect(page).toHaveURL(/\/login$/);

  await page.goto('/vehicles');
  await expect(page).toHaveURL(/\/login$/);
});

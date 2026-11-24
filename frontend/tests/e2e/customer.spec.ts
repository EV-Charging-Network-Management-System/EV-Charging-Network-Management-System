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

test('mobile driver dashboard shows real empty states without horizontal overflow', async ({ page, request }) => {
  const email = `mobile-${crypto.randomUUID()}@example.com`;
  const password = 'BrowserTest123!';
  const registered = await request.post('/api/v1/auth/register', {
    data: { full_name: 'Mobile Driver Test', email, password },
  });
  expect(registered.status()).toBe(201);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/login');
  await page.getByLabel('Email Address').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign In to Network' }).click();
  await expect(page.getByRole('link', { name: 'Find a charger' })).toBeVisible();
  await expect(page.getByText('No upcoming reservations.')).toBeVisible();
  await expect(page.getByText('Add your first vehicle to check connector compatibility.')).toBeVisible();
  expect(await page.locator('body').evaluate(body => body.scrollWidth)).toBeLessThanOrEqual(390);
});

import { expect, test } from '@playwright/test';

import { open, scrollTo, selectWorld, settled } from './support';

const world = (page: import('@playwright/test').Page) =>
  page.evaluate(() =>
    window.__experience.focused ? window.__experience.focusId : null,
  );

test('Back and Forward restore the selected world', async ({ page }) => {
  await open(page);
  await scrollTo(page, 'work');
  await selectWorld(page, 'umbral');
  await expect(page).toHaveURL(/world=umbral/);

  await page.goBack();
  await expect(page).toHaveURL(/^(?!.*world=)/);
  await expect.poll(() => world(page)).toBeNull();

  await page.goForward();
  await expect(page).toHaveURL(/world=umbral/);
  await expect.poll(() => world(page)).toBe('umbral');
});

test('switching worlds updates the entry instead of adding one', async ({
  page,
}) => {
  await open(page);
  await scrollTo(page, 'work');
  await selectWorld(page, 'umbral');
  const length = await page.evaluate(() => history.length);
  await page.keyboard.press('ArrowRight');
  await expect(page).toHaveURL(/world=(?!umbral)\w+/);
  expect(await page.evaluate(() => history.length)).toBe(length);

  await page.goBack();
  await expect.poll(() => world(page)).toBeNull();
});

test('returning to the system leaves no duplicate entry', async ({ page }) => {
  await open(page);
  await scrollTo(page, 'work');
  const length = await page.evaluate(() => history.length);
  await selectWorld(page, 'umbral');
  await page.keyboard.press('Escape');
  await expect(page).toHaveURL(/^(?!.*world=)/);
  await selectWorld(page, 'finance');
  await expect(page).toHaveURL(/world=finance/);
  expect(await page.evaluate(() => history.length)).toBe(length + 1);
});

test('a direct link opens the world and returning keeps the visitor on the page', async ({
  page,
}) => {
  await open(page, '&world=finance');
  await settled(page, 1);
  expect(await world(page)).toBe('finance');
  await expect(page.locator('#world-finance')).toBeVisible();

  await page.keyboard.press('Escape');
  await expect(page).toHaveURL(/^(?!.*world=)/);
  await expect(page.locator('#scene')).toBeVisible();
  expect(await world(page)).toBeNull();
});

test('an unknown world in the url is ignored', async ({ page }) => {
  await open(page, '&world=unknown');
  await expect(page).toHaveURL(/^(?!.*world=)/);
  expect(await world(page)).toBeNull();
});

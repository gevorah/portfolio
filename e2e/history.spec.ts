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

test('remounting the experience does not duplicate its behaviour', async ({
  page,
}) => {
  await open(page);
  for (let index = 0; index < 3; index++) {
    await page.evaluate(() =>
      (window as unknown as { __remount(): void }).__remount(),
    );
    await page.waitForSelector('#scene[data-ready]');
  }
  await scrollTo(page, 'work');
  const length = await page.evaluate(() => history.length);
  await selectWorld(page, 'umbral');
  await settled(page, 1);
  expect(await page.evaluate(() => history.length)).toBe(length + 1);
  await page.keyboard.press('ArrowRight');
  await expect.poll(() => world(page)).toBe('finance');
  await page.waitForTimeout(300);
  expect(await world(page)).toBe('finance');
  await page.keyboard.press('Escape');
  await settled(page, 0);
  await expect(page).toHaveURL(/^(?!.*world=)/);
  expect(await page.evaluate(() => history.length)).toBe(length + 1);
});

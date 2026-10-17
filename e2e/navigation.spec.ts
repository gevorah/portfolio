import { expect, test } from '@playwright/test';

import {
  activate,
  focusedElement,
  open,
  scrollTo,
  sectionTop,
  selectWorld,
  settled,
  VIEWPORTS,
} from './support';

for (const viewport of VIEWPORTS) {
  test.describe(`${viewport.width}px`, () => {
    test.use({ viewport });

    test('navigating to Trayectoria from an open world lands on the section', async ({
      page,
    }) => {
      await open(page);
      await scrollTo(page, 'work');
      await selectWorld(page, 'umbral');
      await settled(page, 1);
      await activate(page, '.site-nav a[href="#experience"]');
      await expect
        .poll(() => sectionTop(page, 'experience'), { timeout: 15_000 })
        .toBe(0);
      await page.waitForTimeout(400);
      expect(await sectionTop(page, 'experience')).toBe(0);
    });

    test('the return control stays inside the viewport', async ({ page }) => {
      await open(page);
      await scrollTo(page, 'work');
      for (const id of ['umbral', 'finance']) {
        await selectWorld(page, id);
        await settled(page, 1);
        await page.waitForTimeout(300);
        await expect(page.locator('[data-return]')).toBeInViewport({
          ratio: 1,
        });
        await page.keyboard.press('Escape');
        await settled(page, 0);
      }
    });
  });
}

test('going to Trabajo from the menu shows the whole system', async ({
  page,
}) => {
  await open(page);
  await scrollTo(page, 'work');
  await selectWorld(page, 'umbral');
  await settled(page, 1);
  await scrollTo(page, 'experience');
  expect(await page.evaluate(() => window.__experience.focused)).toBe(true);
  await activate(page, '.site-nav a[href="#work"]');
  await expect
    .poll(() => sectionTop(page, 'work'), { timeout: 15_000 })
    .toBe(0);
  expect(await page.evaluate(() => window.__experience.focused)).toBe(false);
  await expect(page).toHaveURL(/^(?!.*world=)/);
});

test('focus follows the selected world', async ({ page }) => {
  await open(page);
  await scrollTo(page, 'work');

  const order = await page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>('[data-world-detail]')].map(
      (detail) => detail.dataset.worldDetail!,
    ),
  );

  await page.locator(`[data-world-marker="${order[0]}"]`).focus();
  await page.keyboard.press('Enter');
  expect(await focusedElement(page)).toBe(`world-${order[0]}-title`);

  await page.keyboard.press('ArrowRight');
  expect(await focusedElement(page)).toBe(`world-${order[1]}-title`);

  await page.locator('[data-step="1"]').focus();
  await page.keyboard.press('Enter');
  expect(await focusedElement(page)).toBe('1');
  await expect(page.locator('[data-world-status]')).toContainText(
    `World 3 of ${order.length}`,
  );

  await page.keyboard.press('Escape');
  expect(await focusedElement(page)).toBe(order[0]);
  await expect(page.locator('[data-world-status]')).toContainText(
    'Full system',
  );
});

test('rapid changes leave a consistent state', async ({ page }) => {
  await open(page);
  await scrollTo(page, 'work');
  await selectWorld(page, 'umbral');
  await page.waitForTimeout(120);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(80);
  await selectWorld(page, 'finance');
  await page.waitForTimeout(60);
  await page.keyboard.press('ArrowLeft');
  await page.waitForTimeout(60);
  await page.setViewportSize({ width: 1100, height: 700 });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(40);
  await selectWorld(page, 'finance');
  await settled(page, 1);

  expect(await page.evaluate(() => window.__experience.focusId)).toBe(
    'finance',
  );
  await expect(page.locator('.world-detail[data-active]')).toHaveCount(1);
  await expect(page.locator('#world-finance')).toBeVisible();
  await expect(page).toHaveURL(/world=finance/);

  await page.keyboard.press('Escape');
  await settled(page, 0);
  expect(await page.evaluate(() => window.__experience.focusId)).toBeNull();
  await expect(page.locator('.world-detail[data-active]')).toHaveCount(0);
});

import { expect, test } from '@playwright/test';

import {
  dispatchClick,
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

    test('navigating to Experience from an open world lands on the section', async ({
      page,
    }) => {
      await open(page);
      await scrollTo(page, 'work');
      await selectWorld(page, 'umbral');
      await settled(page, 1);
      await page.locator('.site-nav a[href="#experience"]').click();
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

test('going to Work from the menu shows the whole system', async ({ page }) => {
  await open(page);
  await scrollTo(page, 'work');
  await selectWorld(page, 'umbral');
  await settled(page, 1);
  await scrollTo(page, 'experience');
  expect(await page.evaluate(() => window.__experience.focused)).toBe(true);
  await page.locator('.site-nav a[href="#work"]').click();
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
  await dispatchClick(page, '[data-world-marker="umbral"]');
  await page.waitForTimeout(120);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(80);
  await dispatchClick(page, '[data-world-marker="finance"]');
  await page.waitForTimeout(60);
  await page.keyboard.press('ArrowLeft');
  await page.waitForTimeout(60);
  await page.setViewportSize({ width: 1100, height: 700 });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(40);
  await dispatchClick(page, '[data-world-marker="finance"]');
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

test('keyboard users reach the worlds right after the hero actions', async ({
  page,
}) => {
  await open(page);
  await page.getByRole('link', { name: 'My experience' }).focus();
  await page.keyboard.press('Tab');
  await expect(
    page.getByRole('button', { name: 'Explore Umbral' }),
  ).toBeFocused();
  await page.keyboard.press('Enter');
  await expect
    .poll(() => sectionTop(page, 'work'), { timeout: 15_000 })
    .toBe(0);
  await expect(page.getByRole('heading', { name: 'Umbral' })).toBeFocused();
});

test('section waypoints reflect and change the current section', async ({
  page,
}) => {
  await open(page);
  const waypoints = page.getByRole('navigation', { name: 'Jump to section' });
  await expect(
    waypoints.getByRole('link', { name: 'Universe' }),
  ).toHaveAttribute('aria-current', 'true');
  await waypoints.getByRole('link', { name: 'Experience' }).focus();
  await page.keyboard.press('Enter');
  await expect
    .poll(() => sectionTop(page, 'experience'), { timeout: 15_000 })
    .toBe(0);
  await expect(
    waypoints.getByRole('link', { name: 'Experience' }),
  ).toHaveAttribute('aria-current', 'true');
  await expect(
    waypoints.getByRole('link', { name: 'Universe' }),
  ).not.toHaveAttribute('aria-current', 'true');
  await expect(page.locator('#experience')).toBeFocused();
});

test('going back to Universe closes the open world', async ({ page }) => {
  await open(page);
  await scrollTo(page, 'work');
  await selectWorld(page, 'umbral');
  await settled(page, 1);
  await page.locator('.brand').click();
  await expect
    .poll(() => sectionTop(page, 'universe'), { timeout: 15_000 })
    .toBe(0);
  expect(await page.evaluate(() => window.__experience.focused)).toBe(false);
  await expect(page).toHaveURL(/^(?!.*world=)/);
});

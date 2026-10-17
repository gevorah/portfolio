import { expect, test } from '@playwright/test';

import {
  countDrawCalls,
  drawCallsDuring,
  open,
  scrollTo,
  selectWorld,
} from './support';

test.describe('reduced motion', () => {
  test.use({ reducedMotion: 'reduce' });

  test('nothing is drawn while the scene is at rest', async ({ page }) => {
    await page.addInitScript(countDrawCalls);
    await open(page);
    await page.waitForTimeout(800);
    expect(await drawCallsDuring(page, 1500)).toBe(0);

    await scrollTo(page, 'work');
    await selectWorld(page, 'umbral');
    expect(await page.evaluate(() => window.__experience.focus)).toBe(1);
    await page.waitForTimeout(800);
    expect(await drawCallsDuring(page, 1500)).toBe(0);
  });

  test('the scene still follows scroll and selection', async ({ page }) => {
    await page.addInitScript(countDrawCalls);
    await open(page);
    await page.waitForTimeout(800);
    await page.evaluate(() => (window.__draws = 0));
    await scrollTo(page, 'work');
    expect(await page.evaluate(() => window.__draws)).toBeGreaterThan(0);
  });
});

test('ambient motion renders at a reduced cadence and stops behind Contacto', async ({
  page,
}) => {
  await page.addInitScript(countDrawCalls);
  await open(page);
  await page.waitForTimeout(2500);
  const frames = () => page.evaluate(() => window.__universe.stats.frames);
  const before = await frames();
  await page.waitForTimeout(2000);
  const ambient = (await frames()) - before;
  expect(ambient).toBeGreaterThan(40);
  expect(ambient).toBeLessThan(75);

  await scrollTo(page, 'contact');
  await page.waitForTimeout(2000);
  expect(await drawCallsDuring(page, 1500)).toBe(0);
});

test.describe('adaptive resolution', () => {
  test.use({ deviceScaleFactor: 2 });

  test('resting in Contacto does not lower the resolution', async ({
    page,
  }) => {
    await open(page);
    const width = () =>
      page.evaluate(
        () => document.querySelector<HTMLCanvasElement>('#scene')!.width,
      );
    const initial = await width();
    await scrollTo(page, 'contact');
    await page.waitForTimeout(7000);
    await scrollTo(page, 'universe');
    await page.waitForTimeout(500);
    expect(await width()).toBe(initial);
    expect(await page.evaluate(() => window.__universe.stats.pixelRatio)).toBe(
      2,
    );
  });
});

test('content stays available without WebGL', async ({ page }) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      type: string,
      ...rest: unknown[]
    ) {
      return /webgl/.test(type)
        ? null
        : (original as (...args: unknown[]) => unknown).call(
            this,
            type,
            ...rest,
          );
    } as typeof original;
  });
  await page.goto('/');
  await expect(page.locator('html')).toHaveClass(/no-webgl/);
  await scrollTo(page, 'work');
  await page.getByRole('button', { name: /Umbral/ }).click();
  await expect(page.locator('#world-umbral')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Umbral' })).toBeFocused();
  await scrollTo(page, 'experience');
  await expect(page.getByRole('heading', { name: 'Zelity' })).toBeVisible();
});

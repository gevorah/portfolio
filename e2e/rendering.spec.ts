import { expect, test } from '@playwright/test';

import {
  countDrawCalls,
  drawCallsDuring,
  open,
  sceneCoverage,
  scrollTo,
  selectWorld,
} from './support';

const COMET_COVERAGE = 0.08;
const NEBULA_COVERAGE = 0.03;
const EMPTY_COVERAGE = 0.005;

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

test('ambient motion renders at a reduced cadence and rests in Contact', async ({
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

  test('resting in Contact does not lower the resolution', async ({ page }) => {
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

test('Contact travels on to the nebula and rests without rendering', async ({
  page,
}) => {
  await page.addInitScript(countDrawCalls);
  await open(page);
  const scene = page.locator('#scene');
  const markers = page.locator('.marker:not([data-offstage])');

  await page.locator('.site-nav a[href="#contact"]').click();
  await expect
    .poll(() => page.evaluate(() => window.__experience.zone), {
      timeout: 15_000,
    })
    .toBe('contact');
  await expect(scene).toHaveCSS('opacity', '1');
  await expect(markers).toHaveCount(0);
  await expect
    .poll(() => page.evaluate(() => window.__universe.stats.mode), {
      timeout: 15_000,
    })
    .toBe('idle');
  expect(await drawCallsDuring(page, 1000)).toBe(0);

  await page.locator('.site-nav a[href="#experience"]').click();
  await expect(markers.first()).toBeVisible({ timeout: 15_000 });
  expect(await page.evaluate(() => window.__draws)).toBeGreaterThan(0);
});

test('opening Contact directly composes the nebula', async ({ page }) => {
  await page.goto('/?stats#contact');
  await page.waitForSelector('#scene[data-ready]');
  await expect
    .poll(() => page.evaluate(() => window.__experience.zone))
    .toBe('contact');
  await expect(page.locator('.marker:not([data-offstage])')).toHaveCount(0);
  await expect
    .poll(() => sceneCoverage(page, '.contact .nebula'))
    .toBeGreaterThan(NEBULA_COVERAGE);
});

test('About frames the comet in the shared scene without planets on stage', async ({
  page,
}) => {
  await open(page);
  await page.locator('.site-nav a[href="#about"]').click();
  await expect
    .poll(() => page.evaluate(() => window.__experience.zone), {
      timeout: 15_000,
    })
    .toBe('about');
  await expect(page.locator('#scene')).toHaveCSS('opacity', '1');
  await expect(page.locator('.marker:not([data-offstage])')).toHaveCount(0);
  await expect(page.locator('html')).toHaveAttribute('data-outro', '');
  expect(await page.evaluate(() => window.__universe.stats.mode)).not.toBe(
    'idle',
  );
  await expect
    .poll(() => sceneCoverage(page, '.about .comet'))
    .toBeGreaterThan(COMET_COVERAGE);
  await page.addStyleTag({ content: '#scene { visibility: hidden; }' });
  expect(await sceneCoverage(page, '.about .comet')).toBeLessThan(
    EMPTY_COVERAGE,
  );
});

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 1100, height: 800 },
  { width: 899, height: 700 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
  { width: 320, height: 568 },
]) {
  test(`the comet and the nebula stay visible beside the text at ${viewport.width}×${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await open(page);
    for (const [section, frame, texts, coverage] of [
      ['about', '.about .comet', ['.about-copy'], COMET_COVERAGE],
      [
        'contact',
        '.contact .nebula',
        ['.contact-lede', '.contact-list'],
        NEBULA_COVERAGE,
      ],
    ] as const) {
      await page.evaluate(
        ([id, slot]) =>
          document
            .querySelector(id === 'about' ? slot : `#${id}`)!
            .scrollIntoView({ block: 'center', behavior: 'instant' }),
        [section, frame] as const,
      );
      await expect
        .poll(() => sceneCoverage(page, frame), { timeout: 15_000 })
        .toBeGreaterThan(coverage);
      for (const text of texts)
        expect(await sceneCoverage(page, text), text).toBeLessThan(
          EMPTY_COVERAGE,
        );
    }
  });
}

test.describe('reduced motion in About', () => {
  test.use({ reducedMotion: 'reduce' });

  test('the comet is drawn once and then left at rest', async ({ page }) => {
    await page.addInitScript(countDrawCalls);
    await open(page);
    await scrollTo(page, 'about');
    await page.waitForTimeout(800);
    expect(await sceneCoverage(page, '.about .comet')).toBeGreaterThan(
      COMET_COVERAGE,
    );
    expect(await drawCallsDuring(page, 1500)).toBe(0);
  });
});

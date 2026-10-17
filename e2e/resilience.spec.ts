import { expect, test, type Page } from '@playwright/test';

import { scrollTo } from './support';

const ENTRY = '**/_astro/index.astro_astro_type_script_*.js';

async function expectStaticContent(page: Page) {
  await expect(page.locator('html')).not.toHaveClass(/(^|\s)js(\s|$)/);
  await scrollTo(page, 'work');
  await expect(page.locator('#world-umbral')).toBeVisible();
  await expect(page.locator('#world-finance')).toBeVisible();
  await scrollTo(page, 'experience');
  for (const id of ['icesi', 'zelity'])
    await expect(page.locator(`[data-stage-detail="${id}"]`)).toBeVisible();
  await scrollTo(page, 'contact');
  await expect(page.getByRole('link', { name: /linkedin/i })).toBeVisible();
}

async function expectSceneFallback(page: Page) {
  await expect(page.locator('html')).toHaveClass(/no-webgl/);
  await scrollTo(page, 'work');
  await expect(page.locator('.work-content')).toHaveCSS('opacity', '1');
  await expect(page.locator('.world-index').getByRole('link')).toHaveCount(0);
  await expect(page.locator('.explore-view')).toBeHidden();
  await page.getByRole('button', { name: /^Personal Finance/ }).click();
  await expect(page.locator('#world-finance')).toBeVisible();
  await scrollTo(page, 'experience');
  await page.getByRole('button', { name: /^Encora/ }).click();
  await expect(
    page.locator('.stage-entry[data-active]').getByRole('heading'),
  ).toHaveText('Encora');
}

test('a failed main script keeps the professional content readable', async ({
  page,
}) => {
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  await page.route(ENTRY, (route) => route.fulfill({ status: 503 }));
  await page.goto('/');
  await expectStaticContent(page);
  expect(errors.join('\n')).toContain('interactive layer did not start');
});

test('a missing required element falls back to the static page', async ({
  page,
}) => {
  await page.route('/', async (route) => {
    const response = await route.fetch();
    const html = (await response.text()).replace('data-world-status', '');
    await route.fulfill({ response, body: html });
  });
  await page.goto('/');
  await expectStaticContent(page);
});

test('a failed scene chunk keeps the interactive content', async ({ page }) => {
  await page.route('**/_astro/universe.*.js', (route) => route.abort());
  await page.goto('/');
  await expectSceneFallback(page);
});

test('failed textures keep the interactive content', async ({ page }) => {
  await page.route('**/textures/umbral/**', (route) => route.abort());
  await page.goto('/');
  await expectSceneFallback(page);
});

test('a WebGL context that is never restored falls back', async ({ page }) => {
  await page.goto('/?stats');
  await page.waitForSelector('#scene[data-ready]');
  await page.evaluate(() => {
    const canvas = document.querySelector<HTMLCanvasElement>('#scene')!;
    canvas
      .getContext('webgl2')!
      .getExtension('WEBGL_lose_context')!
      .loseContext();
  });
  await expect(page.locator('html')).not.toHaveClass(/no-webgl/);
  await expect(page.locator('html')).toHaveClass(/no-webgl/, {
    timeout: 5000,
  });
  await expectSceneFallback(page);
});

test.describe('static presentation', () => {
  test.use({
    javaScriptEnabled: false,
    viewport: { width: 1440, height: 900 },
  });

  test('sections start with their introduction beside the details', async ({
    page,
  }) => {
    await page.goto('/');
    const offsets = await page.evaluate(() =>
      (
        [
          ['#work', '.work-prompt', '.work-detail'],
          ['#experience', '.career-intro', '.stage-panel'],
        ] as const
      ).map(([section, intro, detail]) => {
        const top = document.querySelector(section)!.getBoundingClientRect();
        const a = document.querySelector(intro)!.getBoundingClientRect();
        const b = document.querySelector(detail)!.getBoundingClientRect();
        return {
          intro: a.top - top.top,
          detail: b.top - top.top,
          sideBySide: a.right <= b.left,
        };
      }),
    );
    for (const offset of offsets) {
      expect(offset.intro).toBeLessThan(160);
      expect(offset.detail).toBeLessThan(160);
      expect(offset.sideBySide).toBe(true);
    }
  });
});

test('a scene replaced while loading stops before compiling its shaders', async ({
  browser,
}) => {
  const countLinks = () => {
    window.__links = 0;
    const link = WebGL2RenderingContext.prototype.linkProgram;
    WebGL2RenderingContext.prototype.linkProgram = function (program) {
      window.__links += 1;
      return link.call(this, program);
    };
  };
  const linksAfter = async (replace: boolean) => {
    const page = await browser.newPage();
    await page.addInitScript(countLinks);
    let requests = 0;
    await page.route('**/textures/umbral/*.webp', async (route) => {
      requests += 1;
      await new Promise((resolve) => setTimeout(resolve, 1500));
      await route.continue();
    });
    await page.goto('/?stats');
    if (replace) {
      await expect.poll(() => requests).toBe(2);
      await page.evaluate(() =>
        (window as unknown as { __remount(): void }).__remount(),
      );
    }
    await page.waitForSelector('#scene[data-ready]');
    await page.waitForTimeout(1500);
    await expect(page.locator('html')).not.toHaveClass(/no-webgl/);
    const links = await page.evaluate(() => window.__links);
    await page.close();
    return links;
  };
  const single = await linksAfter(false);
  expect(single).toBeGreaterThan(0);
  expect(await linksAfter(true)).toBe(single);
});

import { expect, test, type Page } from '@playwright/test';

import {
  countDrawCalls,
  drawCallsDuring,
  open,
  sampleScene,
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

test('a project opened by URL is framed from the first frame of a late scene', async ({
  page,
}) => {
  await page.route('**/_astro/universe.*.js', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 2500));
    await route.continue();
  });
  await page.goto('/?stats&world=finance');
  await page.addStyleTag({ content: '#scene { transition: none; }' });
  await page.waitForSelector('#scene[data-ready]', { timeout: 20_000 });
  expect(await page.evaluate(() => window.__experience.focus)).toBe(1);
  const first = await sampleScene(page, '#scene');
  await page.waitForTimeout(2000);
  const settled = await sampleScene(page, '#scene');
  expect(Math.abs(first.center.x - settled.center.x)).toBeLessThan(20);
  expect(Math.abs(first.center.y - settled.center.y)).toBeLessThan(20);
});

test('Work hands off to Experience without an empty sky between them', async ({
  page,
}) => {
  await open(page);
  for (const progress of [0.4, 0.45, 0.5]) {
    await page.evaluate((t) => {
      const top = (id: string) =>
        document.getElementById(id)!.getBoundingClientRect().top + scrollY;
      const work = top('work');
      window.scrollTo({
        top: work + (top('experience') - work) * t,
        behavior: 'instant',
      });
    }, progress);
    await page.waitForTimeout(900);
    expect(
      await sceneCoverage(page, '#scene'),
      `t=${progress}`,
    ).toBeGreaterThan(0.0015);
  }
});

test('the hero heading settles into one readable sentence', async ({
  page,
}) => {
  await page.goto('/');
  const heading = page.getByRole('heading', { level: 1 });
  await expect(heading).toHaveAccessibleName(
    "Hi, I'm Jhon, a software engineer.",
  );
  await page.waitForTimeout(2500);
  expect(await page.evaluate(() => document.getAnimations().length)).toBe(0);
  const ink = await page
    .locator('.hero-role .ink')
    .evaluate((element) => getComputedStyle(element));
  expect(ink.backgroundImage).toBe('none');
  expect(ink.color).toBe('rgb(192, 161, 255)');
});

test.describe('reduced motion in the hero', () => {
  test.use({ reducedMotion: 'reduce' });

  test('the hero is shown without an entrance animation', async ({ page }) => {
    await page.goto('/');
    expect(
      await page.evaluate(
        () =>
          document
            .getAnimations()
            .filter((animation) =>
              (animation.effect as KeyframeEffect).target?.closest(
                '.hero-copy',
              ),
            ).length,
      ),
    ).toBe(0);
  });
});

const INTRODUCTIONS = [
  { id: 'about', body: '.about-copy', heading: 'Beyond the code.' },
  { id: 'contact', body: '.contact-body', heading: "Let's talk." },
] as const;

const revealItems = (page: Page, body: string) =>
  page.locator(body).evaluate((element) =>
    [...element.querySelectorAll<HTMLElement>("[style*='--i']")].map((item) => {
      const style = getComputedStyle(item);
      return {
        text: item.textContent!.trim(),
        opacity: Number(style.opacity),
        moved: style.translate !== 'none' && style.translate !== '0px',
        animations: item.getAnimations().length,
      };
    }),
  );

async function expectSettledIntroduction(
  page: Page,
  { body, heading }: (typeof INTRODUCTIONS)[number],
) {
  const items = await revealItems(page, body);
  expect(items.length).toBeGreaterThan(3);
  for (const item of items) {
    expect(item, item.text).toMatchObject({
      opacity: 1,
      moved: false,
      animations: 0,
    });
  }
  const title = page.getByRole('heading', { level: 2, name: heading });
  await expect(title).toBeVisible();
  const box = (await title.boundingBox())!;
  const topmost = await page.evaluate(
    ([x, y]) => document.elementFromPoint(x, y)?.closest('h2')?.textContent,
    [box.x + box.width / 2, box.y + box.height / 2],
  );
  expect(topmost?.replace(/\s+/g, ' ').trim()).toBe(heading);
}

for (const introduction of INTRODUCTIONS) {
  test(`the ${introduction.id} introduction enters once and then stays readable`, async ({
    page,
  }) => {
    await open(page);
    await expect(
      page.getByRole('heading', { level: 2, name: introduction.heading }),
    ).toHaveCount(1);
    const waiting = await revealItems(page, introduction.body);
    expect(waiting.every((item) => item.opacity === 0)).toBe(true);

    await scrollTo(page, introduction.id);
    const entering = await revealItems(page, introduction.body);
    expect(entering.every((item) => item.animations === 1)).toBe(true);
    expect(entering.some((item) => item.opacity < 1)).toBe(true);
    await page
      .locator(introduction.body)
      .evaluate((element) =>
        Promise.all(
          element.getAnimations({ subtree: true }).map((item) => item.finished),
        ),
      );
    await expectSettledIntroduction(page, introduction);

    await scrollTo(page, 'universe');
    await scrollTo(page, introduction.id);
    await expectSettledIntroduction(page, introduction);
  });
}

test.describe('reduced motion in About and Contact', () => {
  test.use({ reducedMotion: 'reduce' });

  for (const introduction of INTRODUCTIONS)
    test(`the ${introduction.id} introduction is shown without an entrance`, async ({
      page,
    }) => {
      await open(page);
      await scrollTo(page, introduction.id);
      await expectSettledIntroduction(page, introduction);
    });
});

import { expect, test, type Page } from '@playwright/test';

import { sectionTop } from './support';

const VIEWPORTS = [
  { width: 320, height: 568 },
  { width: 390, height: 844 },
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
];

const LATE_LAYOUT = `<style id="late-layout">.stage-panel { padding-bottom: 74px; }</style>`;

async function settleLayout(page: Page, after: 'load' | 'manual') {
  const release =
    after === 'load'
      ? `addEventListener('load', () => requestAnimationFrame(() => document.getElementById('late-layout').remove()));`
      : `window.__settle = () => document.getElementById('late-layout').remove();`;
  await page.route(
    (url) => url.pathname === '/',
    async (route) => {
      const response = await route.fetch();
      const body = (await response.text()).replace(
        '</head>',
        `${LATE_LAYOUT}<script>${release}</script></head>`,
      );
      await route.fulfill({ response, body });
    },
  );
}

async function holdFonts(page: Page) {
  let release!: () => void;
  const released = new Promise<void>((resolve) => (release = resolve));
  await page.route(/\.woff2$/, async (route) => {
    await released;
    await route.continue();
  });
  return release;
}

const openFragment = async (page: Page, id: string) => {
  await page.goto(`/#${id}`);
  await page.waitForSelector('#scene[data-ready]');
};

const layoutSettled = (page: Page) =>
  page.waitForFunction(() => !document.getElementById('late-layout'));

const headerBottom = (page: Page) =>
  page
    .locator('.site-header')
    .evaluate((header) => header.getBoundingClientRect().bottom);

const top = (page: Page, selector: string) =>
  page
    .locator(selector)
    .evaluate((element) => element.getBoundingClientRect().top);

async function expectAboutBelowHeader(page: Page) {
  await expect
    .poll(() => sectionTop(page, 'about'), { timeout: 3_000 })
    .toBe(0);
  expect(await top(page, '#about-title')).toBeGreaterThanOrEqual(
    await headerBottom(page),
  );
}

test.describe('reduced motion', () => {
  test.use({ reducedMotion: 'reduce' });

  for (const viewport of VIEWPORTS) {
    test(`an About deep link stays below the header when the layout settles after load at ${viewport.width}×${viewport.height}`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport);
      await settleLayout(page, 'load');
      await openFragment(page, 'about');
      await layoutSettled(page);
      await expectAboutBelowHeader(page);
    });
  }

  for (const viewport of [VIEWPORTS[0], VIEWPORTS[1]]) {
    test(`an About deep link stays below the header when fonts arrive late at ${viewport.width}×${viewport.height}`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport);
      const releaseFonts = await holdFonts(page);
      await page.goto('/#about', { waitUntil: 'domcontentloaded' });
      releaseFonts();
      await page.waitForSelector('#scene[data-ready]');
      await page.evaluate(() => document.fonts.ready);
      await expectAboutBelowHeader(page);
    });
  }

  for (const viewport of [VIEWPORTS[0], VIEWPORTS[1], VIEWPORTS[3]]) {
    test(`a Contact deep link keeps its heading and links visible at ${viewport.width}×${viewport.height}`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport);
      await settleLayout(page, 'load');
      await openFragment(page, 'contact');
      await layoutSettled(page);
      await page.waitForTimeout(300);
      const position = await page.evaluate(() => ({
        top: Math.round(
          document.getElementById('contact')!.getBoundingClientRect().top,
        ),
        atEnd:
          Math.ceil(window.scrollY + window.innerHeight) >=
          document.documentElement.scrollHeight,
      }));
      expect(position.top === 0 || position.atEnd).toBe(true);
      expect(await top(page, '#contact-title')).toBeGreaterThanOrEqual(
        await headerBottom(page),
      );
      await expect(page.locator('#contact-title')).toBeInViewport();
      for (const link of await page.locator('.contact-row').all())
        await expect(link).toBeInViewport();
    });
  }

  for (const [label, scroll] of [
    [
      'with the wheel',
      async (page: Page) => {
        await page.mouse.move(195, 600);
        await page.mouse.wheel(0, 240);
      },
    ],
    [
      'without input events',
      (page: Page) => page.evaluate(() => window.scrollBy(0, 240)),
    ],
  ] as const) {
    test(`a deep link never pulls the page back after the visitor scrolls ${label}`, async ({
      page,
    }) => {
      await page.setViewportSize(VIEWPORTS[1]);
      await settleLayout(page, 'manual');
      const releaseFonts = await holdFonts(page);
      await page.goto('/#about', { waitUntil: 'domcontentloaded' });
      await page.waitForSelector('#scene[data-ready]');
      await scroll(page);
      await expect.poll(() => sectionTop(page, 'about')).toBeLessThan(-200);
      await page.evaluate(() =>
        (window as unknown as { __settle(): void }).__settle(),
      );
      releaseFonts();
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(700);
      expect(await sectionTop(page, 'about')).toBeLessThan(-200);
    });
  }

  test('section navigation after a deep link is not undone', async ({
    page,
  }) => {
    await page.setViewportSize(VIEWPORTS[1]);
    await settleLayout(page, 'load');
    await openFragment(page, 'about');
    await layoutSettled(page);
    await expectAboutBelowHeader(page);
    await page.getByRole('link', { name: 'Work', exact: true }).click();
    await expect
      .poll(() => sectionTop(page, 'work'), { timeout: 3_000 })
      .toBe(0);
    await page.waitForTimeout(700);
    expect(await sectionTop(page, 'work')).toBe(0);
  });

  test('Back and Forward keep returning to the linked sections', async ({
    page,
  }) => {
    await page.setViewportSize(VIEWPORTS[1]);
    await settleLayout(page, 'load');
    await openFragment(page, 'about');
    await layoutSettled(page);
    await expectAboutBelowHeader(page);
    await page.evaluate(() => (window.location.hash = 'experience'));
    await expect
      .poll(() => sectionTop(page, 'experience'), { timeout: 3_000 })
      .toBe(0);
    await page.goBack();
    await expectAboutBelowHeader(page);
    await page.goForward();
    await expect
      .poll(() => sectionTop(page, 'experience'), { timeout: 3_000 })
      .toBe(0);
  });
});

test('with full motion an About deep link is left to native smooth scrolling', async ({
  page,
}) => {
  await page.setViewportSize(VIEWPORTS[1]);
  await page.addInitScript(() => {
    const counted = window as unknown as Record<
      'scrollTo' | 'scrollBy',
      (...args: unknown[]) => void
    > & { __corrections: number };
    counted.__corrections = 0;
    for (const name of ['scrollTo', 'scrollBy'] as const) {
      const native = counted[name].bind(window);
      counted[name] = (...args) => {
        counted.__corrections += 1;
        native(...args);
      };
    }
  });
  await openFragment(page, 'about');
  await expectAboutBelowHeader(page);
  expect(
    await page.evaluate(
      () => (window as unknown as { __corrections: number }).__corrections,
    ),
  ).toBe(0);
});

test('a malformed fragment leaves the interactive page working', async ({
  page,
}) => {
  const errors: Error[] = [];
  page.on('pageerror', (error) => errors.push(error));
  await page.goto('/#%E0%A4%A');
  await page.waitForSelector('#scene[data-ready]');
  await expect(page.locator('html')).toHaveAttribute(
    'data-experience',
    'ready',
  );
  expect(errors).toEqual([]);
});

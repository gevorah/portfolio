import { expect, test, type Page } from '@playwright/test';

import {
  dispatchClick,
  focusedElement,
  open,
  sampleScene,
  sceneCoverage,
  sceneDifference,
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

test('arrow keys with a modifier leave the selected world to the browser', async ({
  page,
}) => {
  await open(page);
  await scrollTo(page, 'work');
  const order = await page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>('[data-world-detail]')].map(
      (detail) => detail.dataset.worldDetail!,
    ),
  );
  await page.evaluate(() => {
    window.__prevented = [];
    window.addEventListener('keydown', (event) =>
      window.__prevented.push(event.defaultPrevented),
    );
  });

  await page.locator(`[data-world-marker="${order[0]}"]`).focus();
  await page.keyboard.press('Enter');
  expect(await focusedElement(page)).toBe(`world-${order[0]}-title`);

  for (const shortcut of [
    'Alt+ArrowRight',
    'Control+ArrowRight',
    'Control+ArrowLeft',
    'Meta+ArrowRight',
    'Shift+ArrowRight',
    'Shift+ArrowLeft',
  ]) {
    await page.keyboard.press(shortcut);
    await expect(
      page.locator(`[data-world-detail="${order[0]}"]`),
      shortcut,
    ).toHaveAttribute('data-active', '');
    expect(await focusedElement(page), shortcut).toBe(
      `world-${order[0]}-title`,
    );
  }

  await page.locator('[data-nav]').first().focus();
  await page.keyboard.press('ArrowRight');
  await expect(
    page.locator(`[data-world-detail="${order[0]}"]`),
  ).toHaveAttribute('data-active', '');

  await page.locator(`#world-${order[0]}-title`).focus();
  await page.keyboard.press('ArrowRight');
  expect(await focusedElement(page)).toBe(`world-${order[1]}-title`);
  await page.keyboard.press('ArrowLeft');
  await page.keyboard.press('ArrowLeft');
  expect(await focusedElement(page)).toBe(`world-${order.at(-1)}-title`);
  expect(await page.evaluate(() => window.__prevented)).not.toContain(true);
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
  ).toHaveAttribute('aria-current', 'location');
  await waypoints.getByRole('link', { name: 'Experience' }).focus();
  await page.keyboard.press('Enter');
  await expect
    .poll(() => sectionTop(page, 'experience'), { timeout: 15_000 })
    .toBe(0);
  await expect(
    waypoints.getByRole('link', { name: 'Experience' }),
  ).toHaveAttribute('aria-current', 'location');
  await expect(
    waypoints.getByRole('link', { name: 'Universe' }),
  ).not.toHaveAttribute('aria-current', 'location');
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

for (const viewport of [
  { width: 1440, height: 500 },
  { width: 390, height: 500 },
]) {
  test(`Contact lands below the header at ${viewport.width}×${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await open(page);
    const headerBottom = await page
      .locator('.site-header')
      .evaluate((header) => header.getBoundingClientRect().bottom);
    const titleTop = () =>
      page
        .locator('#contact-title')
        .evaluate((title) => title.getBoundingClientRect().top);
    const settledTitleTop = async () => {
      await expect
        .poll(
          async () => {
            const before = await page.evaluate(() => scrollY);
            await page.waitForTimeout(200);
            return (await page.evaluate(() => scrollY)) === before;
          },
          { timeout: 15_000 },
        )
        .toBe(true);
      return titleTop();
    };

    const link = page.locator('.site-nav a[href="#contact"]');
    if (await link.isVisible()) {
      await link.click();
      expect(await settledTitleTop()).toBeGreaterThanOrEqual(headerBottom - 1);
      await expect(page.locator('#contact')).toBeFocused();
    }

    await page.goto('/#contact');
    expect(await settledTitleTop()).toBeGreaterThanOrEqual(headerBottom - 1);
  });
}

test('the About fragment lands on its section below the header', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 500 });
  await page.goto('/#about');
  await page.waitForTimeout(600);
  const [headerBottom, noteTop] = await page.evaluate(() => [
    document.querySelector('.site-header')!.getBoundingClientRect().bottom,
    document.querySelector('#about-title')!.getBoundingClientRect().top,
  ]);
  expect(noteTop).toBeGreaterThanOrEqual(headerBottom - 1);
  expect(noteTop).toBeLessThan(500);
});

const SECTIONS = [
  ['universe', 'Universe'],
  ['work', 'Work'],
  ['experience', 'Experience'],
  ['about', 'About'],
  ['contact', 'Contact'],
] as const;

const currentLocations = (page: Page) =>
  page.evaluate(() =>
    ['.waypoints', '.site-nav'].map((selector) =>
      document
        .querySelector(`${selector} [aria-current="location"]`)
        ?.textContent?.trim(),
    ),
  );

test('the five waypoints follow scrolling in both directions and match the header', async ({
  page,
}) => {
  await open(page);
  const waypoints = page.getByRole('navigation', { name: 'Jump to section' });
  await expect(waypoints.getByRole('link')).toHaveCount(SECTIONS.length);
  for (const [id, label] of [...SECTIONS, ...[...SECTIONS].reverse()]) {
    await scrollTo(page, id);
    await expect.poll(() => currentLocations(page)).toEqual([label, label]);
  }
});

test('waypoints follow fragments, history and rapid jumps', async ({
  page,
}) => {
  await page.goto('/#about');
  await page.waitForSelector('#scene[data-ready]');
  await expect.poll(() => currentLocations(page)).toEqual(['About', 'About']);
  await page.goto('/#contact');
  await expect
    .poll(() => currentLocations(page), { timeout: 15_000 })
    .toEqual(['Contact', 'Contact']);
  await page.goBack();
  await expect
    .poll(() => currentLocations(page), { timeout: 15_000 })
    .toEqual(['About', 'About']);
  await expect
    .poll(() => sectionTop(page, 'about'), { timeout: 15_000 })
    .toBe(0);
  await page.goForward();
  await expect
    .poll(() => currentLocations(page), { timeout: 15_000 })
    .toEqual(['Contact', 'Contact']);

  const waypoints = page.getByRole('navigation', { name: 'Jump to section' });
  await waypoints.getByRole('link', { name: 'Work' }).click();
  await expect
    .poll(() => sectionTop(page, 'work'), { timeout: 15_000 })
    .toBe(0);
  await expect.poll(() => currentLocations(page)).toEqual(['Work', 'Work']);
  await expect(page.locator('#work')).toBeFocused();

  for (const name of ['Universe', 'Contact', 'Work', 'About']) {
    await waypoints.getByRole('link', { name }).dispatchEvent('click');
    await page.waitForTimeout(80);
  }
  await expect
    .poll(() => sectionTop(page, 'about'), { timeout: 15_000 })
    .toBe(0);
  await expect.poll(() => currentLocations(page)).toEqual(['About', 'About']);
});

for (const viewport of [
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
  { width: 1440, height: 420 },
]) {
  test(`waypoints leave no controls behind at ${viewport.width}×${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await open(page);
    const links = page
      .getByRole('navigation', { name: 'Jump to section', includeHidden: true })
      .getByRole('link', { includeHidden: true });
    await expect(links).toHaveCount(SECTIONS.length);
    for (const link of await links.all()) await expect(link).toBeHidden();
    const reachable = await page.evaluate(() => {
      const links = [...document.querySelectorAll('.waypoints a')];
      return links.some((link) => {
        (link as HTMLElement).focus();
        return document.activeElement === link;
      });
    });
    expect(reachable).toBe(false);
  });
}

const orbit = (page: Page) =>
  page.evaluate(() => ({ ...window.__experience.orbit }));

async function emptyWorkPoint(page: Page) {
  return page.evaluate(() => {
    for (let y = 150; y < innerHeight - 100; y += 20)
      for (let x = innerWidth * 0.35; x < innerWidth * 0.9; x += 20)
        if (document.elementFromPoint(x, y)?.id === 'work') return { x, y };
    throw new Error('No empty space in Work');
  });
}

const visibleWorlds = (page: Page) =>
  page.evaluate(() =>
    Object.fromEntries(
      [
        ...document.querySelectorAll<HTMLElement>(
          '.world-marker:not([data-offstage])',
        ),
      ].map((marker) => {
        const box = marker.getBoundingClientRect();
        return [
          marker.dataset.worldMarker!,
          { x: box.x + box.width / 2, y: box.y + box.height / 2 },
        ];
      }),
    ),
  );

const largestShift = (
  from: Record<string, { x: number; y: number }>,
  to: Record<string, { x: number; y: number }>,
) =>
  Math.max(
    ...Object.keys(from).map((id) =>
      to[id]
        ? Math.hypot(from[id].x - to[id].x, from[id].y - to[id].y)
        : Infinity,
    ),
  );

async function expectPlanetsUnderMarkers(page: Page) {
  for (const id of ['umbral', 'finance'])
    expect(
      await sceneCoverage(page, `[data-world-marker="${id}"]`),
      `${id} is drawn under its marker`,
    ).toBeGreaterThan(0.08);
}

async function openVisibleWorld(page: Page, id: string) {
  await selectWorld(page, id);
  await settled(page, 1);
  const name = (await page.locator(`#world-${id} h3`).textContent())!.trim();
  await expect(
    page.getByRole('heading', { level: 3, name, exact: true }),
  ).toBeVisible();
  expect(await page.evaluate(() => window.__experience.focusId)).toBe(id);
}

test('dragging rotates the Work view, keeps project selection and resets outside Work', async ({
  page,
}) => {
  await open(page);
  await scrollTo(page, 'work');
  await page.waitForTimeout(800);
  const start = await emptyWorkPoint(page);
  await page.mouse.click(start.x, start.y);
  expect(await orbit(page)).toEqual({ yaw: 0, pitch: 0 });
  await page.evaluate(() => window.__universe.setOrbitTime(80));
  await page.waitForTimeout(400);
  const before = await visibleWorlds(page);

  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  await page.mouse.move(start.x - 200, start.y + 100, { steps: 10 });
  await page.mouse.up();
  const rotated = await orbit(page);
  expect(rotated.yaw).toBeGreaterThan(0);
  expect(rotated.pitch).toBeGreaterThan(0);
  expect(await page.evaluate(() => String(getSelection()))).toBe('');
  await page.waitForTimeout(800);
  expect(largestShift(before, await visibleWorlds(page))).toBeGreaterThan(40);
  await expectPlanetsUnderMarkers(page);

  await selectWorld(page, 'umbral');
  await settled(page, 1);
  await page.keyboard.press('Escape');
  await settled(page, 0);
  expect(await orbit(page)).toEqual(rotated);

  await scrollTo(page, 'experience');
  await expect.poll(() => orbit(page)).toEqual({ yaw: 0, pitch: 0 });
});

test('Explore view turns the visible system, keeps it through a project and resets it', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await open(page);
  await scrollTo(page, 'work');
  await page.evaluate(() => window.__universe.setOrbitTime(80));
  await page.waitForTimeout(400);
  const original = await visibleWorlds(page);
  const originalScene = await sampleScene(page, '#scene');
  await expectPlanetsUnderMarkers(page);

  const toggle = page.getByRole('button', { name: 'Explore view' });
  await toggle.focus();
  await page.keyboard.press('Enter');
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  for (const name of ['Rotate left', 'Rotate left', 'Tilt up', 'Tilt up']) {
    await page.getByRole('button', { name }).focus();
    await page.keyboard.press('Enter');
  }
  await page.waitForTimeout(400);
  const rotated = await visibleWorlds(page);
  const rotatedScene = await sampleScene(page, '#scene');
  expect(largestShift(original, rotated)).toBeGreaterThan(60);
  expect(
    sceneDifference(originalScene.cells, rotatedScene.cells),
  ).toBeGreaterThan(0.3);
  await expectPlanetsUnderMarkers(page);

  await openVisibleWorld(page, 'umbral');
  await page.getByRole('button', { name: 'Back to the system' }).click();
  await settled(page, 0);
  await page.waitForTimeout(400);
  expect(largestShift(rotated, await visibleWorlds(page))).toBeLessThan(2);
  await expectPlanetsUnderMarkers(page);

  await page.getByRole('button', { name: 'Reset view' }).click();
  await page.waitForTimeout(400);
  expect(largestShift(original, await visibleWorlds(page))).toBeLessThan(2);
  await expectPlanetsUnderMarkers(page);

  await openVisibleWorld(page, 'finance');
});

test('touch swipes over Work scroll the page instead of rotating', async ({
  browser,
}) => {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    isMobile: true,
  });
  const page = await context.newPage();
  await open(page);
  await scrollTo(page, 'work');
  await page.waitForTimeout(800);
  const before = await page.evaluate(() => scrollY);
  const cdp = await context.newCDPSession(page);
  await cdp.send('Input.synthesizeScrollGesture', {
    x: 200,
    y: 500,
    yDistance: -300,
    gestureSourceType: 'touch',
  });
  await expect
    .poll(() => page.evaluate(() => scrollY))
    .toBeGreaterThan(before + 100);
  expect(await orbit(page)).toEqual({ yaw: 0, pitch: 0 });
  await context.close();
});

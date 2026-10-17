import { expect, test } from '@playwright/test';

import { open, scrollTo, selectWorld, settled } from './support';

const ORBIT_TIMES = [0, 35, 80, 140, 210, 330, 470];

const overlappingLabels = (page: import('@playwright/test').Page) =>
  page.evaluate(() => {
    const shown = (label: Element) => {
      const style = getComputedStyle(label);
      return style.visibility === 'visible' && Number(style.opacity) > 0;
    };
    const rects = [...document.querySelectorAll<HTMLElement>('.marker')]
      .filter((marker) => shown(marker.querySelector('.marker-label')!))
      .map((marker) => ({
        id: marker.getAttribute('aria-label') ?? marker.textContent!.trim(),
        rect: marker.querySelector('.marker-label')!.getBoundingClientRect(),
      }));
    const pairs: string[] = [];
    rects.forEach((a, index) =>
      rects.slice(index + 1).forEach((b) => {
        if (
          a.rect.left < b.rect.right &&
          a.rect.right > b.rect.left &&
          a.rect.top < b.rect.bottom &&
          a.rect.bottom > b.rect.top
        )
          pairs.push(`${a.id} / ${b.id}`);
      }),
    );
    return pairs;
  });

const hiddenLabelsShown = (page: import('@playwright/test').Page) =>
  page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>('.marker[data-label="hidden"]')]
      .filter(
        (marker) =>
          getComputedStyle(marker.querySelector('.marker-label')!).opacity !==
          '0',
      )
      .map((marker) => marker.textContent!.trim()),
  );

test('label geometry follows the rendered text size', async ({ page }) => {
  await open(page);
  await scrollTo(page, 'work');
  const compare = () =>
    page.evaluate(() => {
      const sizes = window.__universe.inspect().labelSizes;
      return Object.entries(sizes).map(([key, size]) => {
        const selector = key.startsWith('star:')
          ? `[data-star-marker="${key.slice(5)}"]`
          : `[data-world-marker="${key}"]`;
        const label = document.querySelector<HTMLElement>(
          `${selector} .marker-label`,
        )!;
        return <[string, number]>[
          key,
          Math.abs(size.halfWidth * 2 - label.offsetWidth) +
            Math.abs(size.height - label.offsetHeight),
        ];
      });
    });
  for (const [key, error] of await compare()) expect(error, key).toBe(0);
  await page.evaluate(() => (document.documentElement.style.fontSize = '200%'));
  await page.waitForTimeout(300);
  for (const [key, error] of await compare()) expect(error, key).toBe(0);
  const height = await page.evaluate(
    () => window.__universe.inspect().labelSizes.umbral.height,
  );
  expect(height).toBeGreaterThan(30);
});

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`${viewport.width}px`, () => {
    test.use({ viewport });

    test('labels never overlap across orbital positions', async ({ page }) => {
      await open(page);
      for (const section of ['universe', 'work', 'experience']) {
        await scrollTo(page, section);
        for (const time of ORBIT_TIMES) {
          await page.evaluate((t) => window.__universe.setOrbitTime(t), time);
          await page.waitForTimeout(400);
          expect(await overlappingLabels(page), `${section} t=${time}`).toEqual(
            [],
          );
          expect(await hiddenLabelsShown(page), `${section} t=${time}`).toEqual(
            [],
          );
        }
      }
    });

    test('bodies behind the project text are veiled at every orbital position', async ({
      page,
    }) => {
      test.setTimeout(150_000);
      await open(page);
      await scrollTo(page, 'work');
      for (const id of ['umbral', 'finance']) {
        for (const time of ORBIT_TIMES) {
          await page.evaluate((t) => window.__universe.setOrbitTime(t), time);
          await page.waitForTimeout(150);
          await selectWorld(page, id);
          await settled(page, 1);
          await page.waitForTimeout(700);
          const { intruders, veils } = await page.evaluate(() =>
            window.__universe.inspect(),
          );
          for (const intruder of intruders)
            expect(veils[intruder], `${id} t=${time} ${intruder}`).toBe(1);
          await page.keyboard.press('Escape');
          await settled(page, 0);
        }
      }
    });
  });
}

test.describe('label states', () => {
  test.use({ reducedMotion: 'reduce' });

  for (const width of [1440, 899, 390]) {
    test(`a hidden label stays hidden over its variant at ${width}px`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: 844 });
      await open(page);
      await scrollTo(page, 'work');
      await page.waitForTimeout(400);
      const opacity = async (id: string, label: string) => {
        const marker = page.locator(`[data-world-marker="${id}"]`);
        await marker.evaluate(
          (element: HTMLElement, value) => (element.dataset.label = value),
          label,
        );
        await page.waitForTimeout(100);
        return marker
          .locator('.marker-label')
          .evaluate((element) => getComputedStyle(element).opacity);
      };
      expect(Number(await opacity('card-battler', 'below'))).toBeGreaterThan(0);
      expect(await opacity('card-battler', 'hidden')).toBe('0');
      expect(await opacity('umbral', 'hidden')).toBe('0');
    });
  }
});

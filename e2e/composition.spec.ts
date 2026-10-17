import { expect, test } from '@playwright/test';

import { open, scrollTo, selectWorld, settled } from './support';

const ORBIT_TIMES = [0, 35, 80, 140, 210, 330, 470];

const overlappingLabels = (page: import('@playwright/test').Page) =>
  page.evaluate(() => {
    const rects = [...document.querySelectorAll<HTMLElement>('.marker')]
      .filter(
        (marker) =>
          !marker.hasAttribute('data-offstage') &&
          marker.dataset.label !== 'hidden',
      )
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
          await page.waitForTimeout(150);
          expect(await overlappingLabels(page), `${section} t=${time}`).toEqual(
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

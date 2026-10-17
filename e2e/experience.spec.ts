import { expect, test, type Page } from '@playwright/test';

import { careerStages } from '../src/data/career';
import {
  open,
  pointerClick,
  scrollTo,
  selectWorld,
  VIEWPORTS,
} from './support';

const panelBox = (page: Page) =>
  page.evaluate(() => {
    const rect = document
      .querySelector('.stage-panel')!
      .getBoundingClientRect();
    return [Math.round(rect.height), Math.round(window.scrollY)];
  });

const activeHeading = (page: Page) =>
  page.locator('.stage-entry[data-active]').getByRole('heading');

const star = (page: Page, stage: (typeof careerStages)[number]) =>
  page.getByRole('button', { name: `${stage.company}, ${stage.role}` });

const selectedStage = (page: Page) =>
  page.locator('[data-stage-select][aria-pressed="true"] .company');

for (const viewport of VIEWPORTS) {
  test.describe(`${viewport.width}px`, () => {
    test.use({ viewport });

    test('clicking each star shows its stage without moving the layout', async ({
      page,
    }) => {
      await open(page);
      await scrollTo(page, 'experience');
      const before = await panelBox(page);
      for (const stage of careerStages) {
        await pointerClick(page, `[data-star-marker="${stage.id}"]`);
        await expect(activeHeading(page)).toHaveText(stage.company);
        await expect(star(page, stage)).toHaveAttribute('aria-pressed', 'true');
        await expect(page.locator('[data-stage-status]')).toContainText(
          `${stage.company}, ${stage.role}.`,
        );
        expect(await panelBox(page)).toEqual(before);
      }
    });
  });
}

test('previous and next cycle through every stage in order', async ({
  page,
}) => {
  await open(page);
  await scrollTo(page, 'experience');
  const next = page.getByRole('button', { name: 'Next stage' });
  const last = careerStages.at(-1)!;
  await expect(activeHeading(page)).toHaveText(last.company);
  for (const stage of careerStages) {
    await next.click();
    await expect(activeHeading(page)).toHaveText(stage.company);
  }
  await page.getByRole('button', { name: 'Previous stage' }).click();
  await expect(activeHeading(page)).toHaveText(careerStages.at(-2)!.company);
});

test('every star can be reached and selected with the keyboard', async ({
  page,
}) => {
  await open(page);
  await scrollTo(page, 'experience');
  await star(page, careerStages[0]).focus();
  for (const [index, stage] of careerStages.entries()) {
    if (index > 0) await page.keyboard.press('Tab');
    await expect(star(page, stage)).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(activeHeading(page)).toHaveText(stage.company);
  }
});

test('arrow keys step through the stages in chronological order and wrap around', async ({
  page,
}) => {
  await open(page);
  await scrollTo(page, 'experience');
  for (const stage of careerStages) {
    await page.keyboard.press('ArrowRight');
    await expect(activeHeading(page)).toHaveText(stage.company);
    await expect(star(page, stage)).toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('[data-stage-status]')).toContainText(
      `${stage.company}, ${stage.role}.`,
    );
  }
  await page.keyboard.press('ArrowLeft');
  await expect(activeHeading(page)).toHaveText(careerStages.at(-2)!.company);
  await page.keyboard.press('ArrowRight');
  await page.keyboard.press('ArrowRight');
  await expect(activeHeading(page)).toHaveText(careerStages[0].company);
  await page.keyboard.press('ArrowLeft');
  await expect(activeHeading(page)).toHaveText(careerStages.at(-1)!.company);
});

test('arrow keys keep focus on the focused stage control', async ({ page }) => {
  await open(page);
  await scrollTo(page, 'experience');
  const [first, second, third] = careerStages;
  await star(page, first).focus();
  await page.keyboard.press('Enter');
  await page.keyboard.press('ArrowRight');
  await expect(activeHeading(page)).toHaveText(second.company);
  await expect(star(page, first)).toBeFocused();
  const next = page.getByRole('button', { name: 'Next stage' });
  await next.focus();
  await page.keyboard.press('ArrowRight');
  await expect(activeHeading(page)).toHaveText(third.company);
  await expect(next).toBeFocused();
});

test('arrow keys only step stages from within Experience', async ({ page }) => {
  await open(page);
  const last = careerStages.at(-1)!;
  await scrollTo(page, 'work');
  const worlds = await page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>('[data-world-detail]')].map(
      (detail) => detail.dataset.worldDetail!,
    ),
  );
  await selectWorld(page, worlds[0]);
  await page.keyboard.press('ArrowRight');
  await expect(
    page.locator(`[data-world-detail="${worlds[1]}"]`),
  ).toHaveAttribute('data-active', '');
  await expect(selectedStage(page)).toHaveText(last.company);
  await page.keyboard.press('Escape');

  await scrollTo(page, 'universe');
  await page.keyboard.press('ArrowRight');
  await expect(selectedStage(page)).toHaveText(last.company);

  await scrollTo(page, 'experience');
  await page.locator('[data-nav]').first().focus();
  await page.keyboard.press('ArrowRight');
  await expect(selectedStage(page)).toHaveText(last.company);

  await page.evaluate(() => (document.activeElement as HTMLElement).blur());
  for (const shortcut of ['Alt+ArrowRight', 'Shift+ArrowRight']) {
    await page.keyboard.press(shortcut);
    await expect(selectedStage(page)).toHaveText(last.company);
  }
  await page.keyboard.press('ArrowRight');
  await expect(selectedStage(page)).toHaveText(careerStages[0].company);
});

import { expect, test } from '@playwright/test';

import { careerStages } from '../src/data/career';
import { profile } from '../src/data/profile';
import { worlds } from '../src/data/worlds';

test.use({ javaScriptEnabled: false });

test('the page is published in English with the profile introduction', async ({
  page,
}) => {
  await page.goto('/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  const heading = page.getByRole('heading', { level: 1 });
  await expect(heading).toContainText(profile.name);
  await expect(heading).toContainText(profile.title.toLowerCase());
  await expect(page.locator('.hero-summary')).toHaveText(profile.summary);
});

test('every world renders its content', async ({ page }) => {
  await page.goto('/');
  for (const world of worlds) {
    const detail = page.locator(`#world-${world.id}`);
    await expect(detail.getByRole('heading')).toHaveText(world.name);
    await expect(detail.locator('.world-tagline')).toHaveText(world.tagline);
    await expect(detail.locator('.prose')).toHaveText(world.description);
  }
});

test('every career stage renders its role, period and technologies', async ({
  page,
}) => {
  await page.goto('/');
  for (const stage of careerStages) {
    const entry = page.locator(`[data-stage-detail="${stage.id}"]`);
    await expect(entry.getByRole('heading')).toHaveText(stage.company);
    await expect(entry.locator('[data-role]')).toHaveText(stage.role);
    await expect(entry.locator('.period')).toHaveText(stage.period);
    await expect(entry.locator('.summary')).toHaveText(stage.summary);
    await expect(entry.locator('.stage-tech li')).toHaveText(
      stage.technologies,
    );
  }
});

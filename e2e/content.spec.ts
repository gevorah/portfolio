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

test('About is its own section with education and location', async ({
  page,
}) => {
  await page.goto('/');
  const about = page.locator('section#about');
  await expect(about.getByRole('heading', { level: 2 })).toHaveText(
    'Beyond the code.',
  );
  await expect(about.locator('.about-text')).toHaveText(
    `${profile.about.lead} ${profile.about.emphasis}`,
  );
  const details = about.locator('.about-details');
  await expect(details).toContainText(profile.education.degree);
  await expect(details).toContainText(profile.education.institution);
  await expect(details).toContainText(profile.education.year);
  await expect(details).toContainText(profile.location);
  await expect(page.locator('#experience')).not.toContainText(
    profile.education.degree,
  );
});

test('Contact lists every channel as a labelled row', async ({ page }) => {
  await page.goto('/');
  const contact = page.locator('#contact');
  await expect(contact.getByRole('heading', { level: 2 })).toHaveText(
    "Let's talk.",
  );
  const rows = contact.locator('.contact-row');
  await expect(rows).toHaveCount(profile.contact.length);
  for (const [index, channel] of profile.contact.entries()) {
    const row = rows.nth(index);
    await expect(row).toHaveAttribute('href', channel.href);
    await expect(row).toContainText(channel.label);
    await expect(row).toContainText(channel.value);
    if (channel.href.startsWith('http')) {
      await expect(row).toHaveAttribute('target', '_blank');
      await expect(row).toHaveAttribute('rel', 'noopener noreferrer');
      await expect(row).toContainText('(opens in a new tab)');
    }
  }
  await expect(rows.first()).toHaveAttribute(
    'href',
    /^mailto:jhon\.ijaji\.o@gmail\.com$/,
  );
});

for (const { label, viewport, fontSize } of [
  { label: 'desktop', viewport: { width: 1080, height: 743 }, fontSize: 16 },
  { label: 'mobile', viewport: { width: 390, height: 844 }, fontSize: 16 },
  { label: 'zoomed', viewport: { width: 720, height: 450 }, fontSize: 16 },
  {
    label: 'enlarged text',
    viewport: { width: 390, height: 844 },
    fontSize: 32,
  },
]) {
  test(`the project index lands each project below the header (${label})`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('Page.setFontSizes', { fontSizes: { standard: fontSize } });
    await page.goto('/');
    const index = page.locator('.world-index');
    await expect(index.getByRole('button')).toHaveCount(0);
    const links = index.getByRole('link');
    await expect(links).toHaveCount(worlds.length);
    for (const world of worlds) {
      await links.filter({ hasText: world.name }).focus();
      await page.keyboard.press('Enter');
      await expect(page).toHaveURL(new RegExp(`#world-${world.id}$`));
      const [header, meta, heading] = await page.evaluate((id) => {
        const article = document.getElementById(`world-${id}`)!;
        return [
          document.querySelector('.site-header')!,
          article.querySelector('.world-meta')!,
          article.querySelector('h3')!,
        ].map((element) => element.getBoundingClientRect());
      }, world.id);
      expect(meta.top).toBeGreaterThanOrEqual(header.bottom);
      expect(heading.bottom).toBeLessThanOrEqual(viewport.height);
    }
  });
}

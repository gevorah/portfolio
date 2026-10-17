import type { Page } from '@playwright/test';

declare global {
  interface Window {
    __draws: number;
    __experience: {
      focused: boolean;
      focusId: string | null;
      focus: number;
      zone: string;
      stageId: string;
    };
    __universe: {
      stats: { pixelRatio: number; mode: string; frames: number };
      setOrbitTime(seconds: number): void;
      inspect(): {
        intruders: string[];
        veils: Record<string, number>;
        labels: Record<string, string>;
      };
    };
  }
}

export const VIEWPORTS = [
  { width: 1440, height: 900 },
  { width: 1024, height: 768 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
  { width: 320, height: 568 },
];

export async function open(page: Page, query = '') {
  await page.goto(`/?stats${query}`);
  await page.waitForSelector('#scene[data-ready]');
}

export async function scrollTo(page: Page, id: string) {
  await page.evaluate(
    (target) =>
      document.getElementById(target)!.scrollIntoView({ behavior: 'instant' }),
    id,
  );
  await page.waitForTimeout(250);
}

export const activate = (page: Page, selector: string) =>
  page.locator(selector).evaluate((element: HTMLElement) => element.click());

export const selectWorld = (page: Page, id: string) =>
  activate(page, `[data-world-marker="${id}"]`);

export const settled = (page: Page, target: 0 | 1) =>
  page.waitForFunction((value) => {
    const { focus, focused, focusId } = window.__experience;
    return value === 1
      ? focused && focus === 1
      : !focused && focus === 0 && focusId === null;
  }, target);

export const focusedElement = (page: Page) =>
  page.evaluate(() => {
    const element = document.activeElement as HTMLElement;
    return (
      element.id ||
      element.dataset.worldMarker ||
      element.dataset.step ||
      element.tagName
    );
  });

export const sectionTop = (page: Page, id: string) =>
  page.evaluate(
    (target) =>
      Math.round(
        document.getElementById(target)!.getBoundingClientRect().top,
      ) || 0,
    id,
  );

export function countDrawCalls() {
  window.__draws = 0;
  const proto = WebGL2RenderingContext.prototype;
  for (const name of [
    'drawArrays',
    'drawElements',
    'drawArraysInstanced',
    'drawElementsInstanced',
  ] as const) {
    const original = proto[name] as (...args: unknown[]) => void;
    (proto as unknown as Record<string, unknown>)[name] = function (
      this: WebGL2RenderingContext,
      ...args: unknown[]
    ) {
      window.__draws += 1;
      return original.apply(this, args);
    };
  }
}

export async function drawCallsDuring(page: Page, ms: number) {
  await page.evaluate(() => (window.__draws = 0));
  await page.waitForTimeout(ms);
  return page.evaluate(() => window.__draws);
}

const LIT_LUMINANCE = 48;

export async function sampleScene(page: Page, selector: string) {
  const overlay = await page.addStyleTag({
    content:
      '.site-main, .site-header, .waypoints { visibility: hidden !important; }',
  });
  const clip = await page.locator(selector).evaluate((element) => {
    const rect = element.getBoundingClientRect();
    const x = Math.max(0, rect.left);
    const y = Math.max(0, rect.top);
    return {
      x,
      y,
      width: Math.min(innerWidth, rect.right) - x,
      height: Math.min(innerHeight, rect.bottom) - y,
    };
  });
  const image = (await page.screenshot({ clip })).toString('base64');
  await overlay.evaluate((style) => (style as Element).remove());
  const sample = await page.evaluate(
    async ([data, threshold]) => {
      const blob = await (await fetch(`data:image/png;base64,${data}`)).blob();
      const bitmap = await createImageBitmap(blob);
      const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
      const context = canvas.getContext('2d')!;
      context.drawImage(bitmap, 0, 0);
      const { data: pixels, width } = context.getImageData(
        0,
        0,
        bitmap.width,
        bitmap.height,
      );
      let lit = 0;
      let weight = 0;
      let sumX = 0;
      let sumY = 0;
      for (let index = 0; index < pixels.length; index += 4) {
        const luminance =
          0.2126 * pixels[index] +
          0.7152 * pixels[index + 1] +
          0.0722 * pixels[index + 2];
        if (luminance <= threshold) continue;
        const pixel = index / 4;
        lit += 1;
        weight += luminance;
        sumX += (pixel % width) * luminance;
        sumY += Math.floor(pixel / width) * luminance;
      }
      return {
        coverage: lit / (bitmap.width * bitmap.height),
        center: { x: sumX / weight, y: sumY / weight },
      };
    },
    [image, LIT_LUMINANCE] as const,
  );
  return {
    coverage: sample.coverage,
    center: { x: clip.x + sample.center.x, y: clip.y + sample.center.y },
  };
}

export const sceneCoverage = async (page: Page, selector: string) =>
  (await sampleScene(page, selector)).coverage;

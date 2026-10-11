// Renders an SVG or HTML file to PNG with the pre-installed Chromium.
// usage: node render.mjs <input> <output.png> [width] [height] [scale]
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)(process.env.PW_PATH || 'playwright');
import path from 'node:path';

const [input, output, w = '1600', h = '1000', scale = '1'] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: +w, height: +h },
  deviceScaleFactor: +scale
});
await page.goto('file://' + path.resolve(input));
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(300);
await page.screenshot({ path: output });
await browser.close();

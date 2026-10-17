import { defineConfig } from '@playwright/test';

const PORT = 4329;

export default defineConfig({
  testDir: 'e2e',
  fullyParallel: true,
  workers: 2,
  reporter: 'list',
  timeout: 45_000,
  use: {
    baseURL: `http://localhost:${PORT}`,
    channel: 'chrome',
    viewport: { width: 1440, height: 900 },
  },
  webServer: {
    command: `pnpm build && node e2e/serve.mjs ${PORT}`,
    url: `http://localhost:${PORT}`,
    reuseExistingServer: false,
    timeout: 120_000,
  },
});

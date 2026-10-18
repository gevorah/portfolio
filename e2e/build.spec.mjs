import { readFile } from 'node:fs/promises';
import { expect, test } from '@playwright/test';

test('the suite runs against the build of this checkout', async ({
  request,
}) => {
  const built = await readFile(
    new URL('../dist/index.html', import.meta.url),
    'utf8',
  );
  const served = await (await request.get('/')).text();
  expect(served).toBe(built);
});

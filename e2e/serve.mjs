import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../dist', import.meta.url));
const port = Number(process.argv[2] ?? 4329);
const types = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.webp': 'image/webp',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

createServer((request, response) => {
  const pathname = decodeURIComponent(
    new URL(request.url, 'http://x').pathname,
  );
  let file = join(root, normalize(pathname));
  if (!file.startsWith(root)) file = root;
  if (existsSync(file) && statSync(file).isDirectory())
    file = join(file, 'index.html');
  if (!existsSync(file)) {
    response.writeHead(404).end('Not found');
    return;
  }
  response.writeHead(200, {
    'content-type': types[extname(file)] ?? 'application/octet-stream',
  });
  createReadStream(file).pipe(response);
}).listen(port, () => console.log(`dist served at http://localhost:${port}`));

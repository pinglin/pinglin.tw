import { existsSync, readdirSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

export const root = dirname(dirname(fileURLToPath(import.meta.url)));
export const output = join(root, 'dist', 'client');

export function walk(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => (entry.isDirectory() ? walk(join(dir, entry.name)) : [join(dir, entry.name)]));
}

// Public URL path of a built file: .../x/index.html -> /x/, .../x.png -> /x.png
export function publicPath(file) {
  return `/${relative(output, file).split(sep).join('/')}`.replace(/index\.html$/, '');
}

// Built file behind a public URL path: /x/ -> .../x/index.html, /x.png -> .../x.png
export function builtFile(pathname) {
  const path = decodeURIComponent(pathname);
  return join(output, path, path.endsWith('/') ? 'index.html' : '');
}

export function isBuilt(pathname) {
  return existsSync(builtFile(pathname));
}

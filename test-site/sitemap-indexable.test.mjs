import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import { URL } from 'node:url';

import { builtFile, isBuilt, output, root } from './helpers.mjs';

// A sitemap submits URLs for indexing, so a noindex page in one draws Search
// Console's "Submitted URL marked noindex". robots.txt advertises the
// integration's sitemap-index.xml (which only points at sitemap-0.xml) and the
// hand-written sitemap.xml, so both page lists are checked.
const sitemaps = readdirSync(output).filter((name) => /^sitemap.*\.xml$/.test(name) && name !== 'sitemap-index.xml');
const listed = Object.fromEntries(
  sitemaps.map((name) => [
    name,
    [...readFileSync(join(output, name), 'utf8').matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => new URL(match[1]).pathname),
  ]),
);

function isNoindex(html) {
  return [...html.matchAll(/<meta\b[^>]*>/gi)].some(([tag]) => /\bname=["']robots["']/i.test(tag) && /\bcontent=["'][^"']*\bnoindex\b/i.test(tag));
}

// English posts that production builds with no zh-tw translation. Each keeps a
// /zh-tw/blog/<slug>/ stub that redirects to the English post (so the zh-tw URL
// does not 404) and carries noindex.
const blogDir = join(root, 'src', 'content', 'blog');
const translated = new Set(readdirSync(join(blogDir, 'zh-tw')));
const englishOnly = readdirSync(blogDir)
  .filter((name) => name.endsWith('.md') && !translated.has(name))
  .filter((name) => {
    const frontmatter = readFileSync(join(blogDir, name), 'utf8').match(/^---\n([\s\S]*?)\n---/)?.[1] ?? '';
    return !/^draft:\s*true\s*$/m.test(frontmatter);
  })
  .map((name) => name.replace(/\.md$/, ''));

test('every sitemap URL is a built page that is not noindex', () => {
  assert.ok(sitemaps.includes('sitemap-0.xml') && sitemaps.includes('sitemap.xml'), `found ${sitemaps}`);
  for (const [name, paths] of Object.entries(listed)) {
    assert.ok(paths.length > 0, `${name} lists no URLs`);
    const pages = paths.filter((path) => isBuilt(path) && builtFile(path).endsWith('.html'));
    assert.deepEqual(
      paths.filter((path) => !pages.includes(path)),
      [],
      `${name} lists URLs that are not built pages`,
    );
    assert.deepEqual(
      pages.filter((path) => isNoindex(readFileSync(builtFile(path), 'utf8'))),
      [],
      `${name} lists noindex pages`,
    );
  }
});

test('English-only posts keep their noindex /zh-tw/blog/ stub', () => {
  for (const slug of englishOnly) {
    const stub = `/zh-tw/blog/${slug}/`;
    assert.ok(isBuilt(stub), `${stub} should still build`);
    assert.ok(isNoindex(readFileSync(builtFile(stub), 'utf8')), `${stub} should be noindex`);
  }
});

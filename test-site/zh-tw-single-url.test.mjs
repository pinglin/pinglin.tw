import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, relative, sep } from 'node:path';
import test from 'node:test';
import { fileURLToPath, URL } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const output = join(root, 'dist', 'client');
const vercelConfig = JSON.parse(readFileSync(join(root, 'vercel.json'), 'utf8'));

// Translations that production builds: every src/content/blog/zh-tw post that
// is not a draft. Hidden posts still build; they only stay out of indexes.
const zhDir = join(root, 'src', 'content', 'blog', 'zh-tw');
const translations = readdirSync(zhDir)
  .filter((name) => name.endsWith('.md'))
  .map((name) => {
    const frontmatter = readFileSync(join(zhDir, name), 'utf8').match(/^---\n([\s\S]*?)\n---/)?.[1] ?? '';
    return {
      slug: name.replace(/\.md$/, ''),
      draft: /^draft:\s*true\s*$/m.test(frontmatter),
      hidden: /^hidden:\s*true\s*$/m.test(frontmatter),
    };
  })
  .filter(({ draft }) => !draft);

function walk(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => (entry.isDirectory() ? walk(join(dir, entry.name)) : [join(dir, entry.name)]));
}

// Public URL path of a built file: .../x/index.html -> /x/, .../x.png -> /x.png
function publicPath(file) {
  return `/${relative(output, file).split(sep).join('/')}`.replace(/index\.html$/, '');
}

function isBuilt(pathname) {
  const path = decodeURIComponent(pathname);
  return existsSync(join(output, path, path.endsWith('/') ? 'index.html' : ''));
}

test('translations build under /zh-tw/blog/ only, never /blog/zh-tw/', () => {
  assert.ok(translations.length > 0);
  assert.ok(!existsSync(join(output, 'blog', 'zh-tw')), 'dist/client/blog/zh-tw/ must not be built');
  assert.ok(!existsSync(join(output, 'og', 'blog', 'zh-tw')), 'dist/client/og/blog/zh-tw/ must not be built');
  for (const { slug } of translations) {
    assert.ok(existsSync(join(output, 'zh-tw', 'blog', slug, 'index.html')), `missing /zh-tw/blog/${slug}/`);
  }
});

test('sitemaps and llms.txt list each translation once, at /zh-tw/blog/', () => {
  // robots.txt advertises both the integration's sitemap-index.xml and the
  // hand-written sitemap.xml, so every sitemap file is checked.
  const sitemaps = readdirSync(output).filter((name) => /^sitemap.*\.xml$/.test(name));
  assert.ok(sitemaps.includes('sitemap.xml') && sitemaps.includes('sitemap-0.xml'), `found ${sitemaps}`);

  const listed = {
    ...Object.fromEntries(
      sitemaps.map((name) => {
        const xml = readFileSync(join(output, name), 'utf8');
        return [name, [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => new URL(match[1]))];
      }),
    ),
    'llms.txt': [...readFileSync(join(output, 'llms.txt'), 'utf8').matchAll(/\]\((https:\/\/pinglin\.tw\/[^)]*)\)/g)].map(
      (match) => new URL(match[1]),
    ),
  };

  for (const [name, urls] of Object.entries(listed)) {
    const paths = urls.map((url) => url.pathname);
    assert.deepEqual(
      paths.filter((path) => path.startsWith('/blog/zh-tw/')),
      [],
      `${name} lists the duplicate /blog/zh-tw/ path`,
    );
    assert.deepEqual(
      paths.filter((path) => !isBuilt(path)),
      [],
      `${name} lists URLs that are not built pages`,
    );
    if (name === 'sitemap-index.xml') continue;
    for (const { slug, hidden } of translations) {
      if (hidden) continue;
      assert.equal(paths.filter((path) => path === `/zh-tw/blog/${slug}/`).length, 1, `${name} should list /zh-tw/blog/${slug}/ once`);
    }
  }
});

test('every formerly live /blog/zh-tw/ URL 308s to its /zh-tw/blog/ page', () => {
  // Compile vercel.json with the same router compiler the Vercel adapter uses,
  // so the patterns are checked as production runs them. In particular, the
  // strict matcher means a bare `/blog/zh-tw/:path*` source never matches the
  // trailing-slash URLs that were indexed.
  const requireFromAdapter = createRequire(createRequire(import.meta.url).resolve('@astrojs/vercel'));
  const { getTransformedRoutes } = requireFromAdapter('@vercel/routing-utils');
  const { routes, error } = getTransformedRoutes({ trailingSlash: vercelConfig.trailingSlash, redirects: vercelConfig.redirects });
  assert.equal(error, null);

  // Follow redirects the way the router does: the first matching route wins.
  function follow(path) {
    const statuses = [];
    for (let hop = 0; hop < 5; hop += 1) {
      const route = routes.find(({ src, headers }) => headers?.Location && new RegExp(src).test(path));
      if (!route) break;
      const match = path.match(new RegExp(route.src));
      statuses.push(route.status);
      path = route.headers.Location.replace(/\$(\d+)/g, (_, group) => match[group] ?? '');
    }
    return { path, statuses };
  }

  for (const { slug } of translations) {
    const pages = walk(join(output, 'zh-tw', 'blog', slug)).filter((file) => file.endsWith('index.html'));
    const images = walk(join(output, 'og', 'zh-tw', 'blog', slug)).filter((file) => file.endsWith('.png'));
    assert.ok(pages.length > 1 && images.length > 0, `expected sections and OG images for ${slug}`);

    for (const target of [...pages, ...images].map(publicPath)) {
      const legacy = target.replace(/^(\/og)?\/zh-tw\/blog\//, '$1/blog/zh-tw/');
      const forms = target.endsWith('/') ? [legacy, legacy.slice(0, -1)] : [legacy];
      for (const form of forms) {
        const { path, statuses } = follow(form);
        assert.equal(path, target, `${form} should land on ${target}`);
        assert.ok(statuses.length > 0 && statuses.every((status) => status === 308), `${form}: ${statuses}`);
      }
    }
  }

  // English posts are untouched.
  assert.deepEqual(follow('/blog/the-shapes-of-agent-memory/'), { path: '/blog/the-shapes-of-agent-memory/', statuses: [] });
});

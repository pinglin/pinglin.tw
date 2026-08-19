import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath, URL } from 'node:url';
import { dirname, join } from 'node:path';
import test from 'node:test';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const output = join(root, 'dist', 'client');
const astroConfigSource = readFileSync(join(root, 'astro.config.mjs'), 'utf8');
const tableOfContentsSource = readFileSync(join(root, 'src', 'components', 'TableOfContents.astro'), 'utf8');
const vercelConfig = JSON.parse(readFileSync(join(root, 'vercel.json'), 'utf8'));

function meta(html, property) {
  return html.match(new RegExp(`<meta[^>]+property=["']${property.replace(':', '\\:')}["'][^>]+content=["']([^"']+)["']`, 'i'))?.[1];
}

function link(html, rel) {
  return html.match(new RegExp(`<link[^>]+rel=["']${rel}["'][^>]+href=["']([^"']+)["']`, 'i'))?.[1];
}

function articleFixture(articlePath) {
  const articleDir = join(output, articlePath);
  return {
    articleDir,
    html: readFileSync(join(articleDir, 'index.html'), 'utf8'),
  };
}

test('every English article heading has a crawler-visible section permalink and OG snapshot', () => {
  const articleSlug = 'the-shapes-of-agent-memory';
  const articlePath = `blog/${articleSlug}`;
  const { articleDir, html: articleHtml } = articleFixture(articlePath);
  const sectionIds = [...articleHtml.matchAll(/data-section-id=["']([^"']+)["']/g)].map((match) => match[1]);

  assert.ok(sectionIds.length > 0, 'the article should render section copy controls');
  assert.ok(sectionIds.includes('store-architectures'));
  assert.equal(new Set(sectionIds).size, sectionIds.length);

  for (const sectionId of sectionIds) {
    const publicArticlePath = `/${articlePath}/`;
    const publicSectionPath = `${publicArticlePath}sections/${sectionId}/`;
    const sectionDir = join(articleDir, 'sections', sectionId);
    const htmlPath = join(sectionDir, 'index.html');
    assert.ok(existsSync(htmlPath), `missing section page ${publicSectionPath}`);

    const html = readFileSync(htmlPath, 'utf8');
    const expectedUrl = `https://pinglin.tw${publicSectionPath}`;
    const expectedImagePath = `/og/${articlePath}/sections/${sectionId}.png`;
    assert.equal(meta(html, 'og:url'), expectedUrl);

    const ogImage = new URL(meta(html, 'og:image'));
    assert.equal(ogImage.origin, 'https://pinglin.tw');
    assert.equal(ogImage.pathname, expectedImagePath);
    assert.match(ogImage.search, /^\?v=[a-f0-9]{10}$/);
    assert.equal(link(html, 'canonical'), `https://pinglin.tw${publicArticlePath}`);
    assert.match(html, new RegExp(`data-active-section=["']${sectionId}["']`));
    assert.match(html, new RegExp(`id=["']${sectionId}["']`));

    const imagePath = join(output, expectedImagePath);
    assert.ok(existsSync(imagePath), `missing OG snapshot ${expectedImagePath}`);
    const png = readFileSync(imagePath);
    assert.equal(png.toString('hex', 0, 8), '89504e470d0a1a0a');
    assert.equal(png.readUInt32BE(16), 1200);
    assert.equal(png.readUInt32BE(20), 630);
  }

  assert.equal(meta(articleHtml, 'og:image'), `https://pinglin.tw/blog/${articleSlug}/header_light.png`);
  assert.match(articleHtml, /data-article-url=/);
  assert.match(articleHtml, /location\.hash/);
  assert.match(articleHtml, /history\.replaceState/);
  assert.match(articleHtml, /navigator\.clipboard/);
});

test('Traditional Chinese headings receive localized section permalinks', () => {
  const articleSlug = 'collection-autofill-at-scale';
  const articlePath = `zh-tw/blog/${articleSlug}`;
  const { articleDir, html } = articleFixture(articlePath);
  const sectionId = '先談一下-collections';
  const sectionPath = join(articleDir, 'sections', sectionId, 'index.html');

  assert.match(html, new RegExp(`data-section-id=["']${sectionId}["']`));
  assert.ok(existsSync(sectionPath));
  const sectionHtml = readFileSync(sectionPath, 'utf8');
  assert.equal(meta(sectionHtml, 'og:url'), new URL(`/${articlePath}/sections/${sectionId}/`, 'https://pinglin.tw').href);
  assert.ok(existsSync(join(output, 'og', articlePath, 'sections', `${sectionId}.png`)));
});

test('noncanonical section permalinks stay out of the generated sitemap', () => {
  const sitemap = readFileSync(join(output, 'sitemap-0.xml'), 'utf8');
  assert.doesNotMatch(sitemap, /\/sections\//);
});

test('table-of-contents navigation preserves section permalinks', () => {
  assert.match(tableOfContentsSource, /link\.dataset\.sectionPath = sectionPath/);
  assert.match(tableOfContentsSource, /sectionPathFor\(targetElement, targetId\)/);
  assert.doesNotMatch(tableOfContentsSource, /className = 'header-link'/);
  assert.doesNotMatch(tableOfContentsSource, /header\.innerHTML = ''/);
});

test('deployment canonicalizes extensionless URLs with a trailing slash', () => {
  // Vercel issues the 308 that keeps one crawler-visible identity per section.
  assert.equal(vercelConfig.trailingSlash, true);
  // Astro stays permissive so both forms resolve locally; a dev-time 404 on the
  // no-slash form buys nothing that the production redirect does not already.
  assert.match(astroConfigSource, /trailingSlash:\s*'ignore'/);
});

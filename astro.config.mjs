import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel';
import preact from '@astrojs/preact';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';
import mermaid from 'astro-mermaid';
import { visit } from 'unist-util-visit';

import { languages, defaultLang } from './src/i18n/ui';

const supportedLanguages = Object.keys(languages);

// Collect the basenames of blog posts marked `hidden: true` in frontmatter, so
// the auto-generated sitemap can drop them (they stay reachable by direct URL
// but are excluded from listings, RSS, and sitemap alike). Keeps the `hidden`
// flag the single source of truth instead of hardcoding slugs here.
function collectHiddenSlugs(dir) {
  const hidden = new Set();
  const walk = (d) => {
    for (const entry of readdirSync(d, { withFileTypes: true })) {
      const full = join(d, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith('.md')) {
        const fm = readFileSync(full, 'utf-8').match(/^---\n([\s\S]*?)\n---/);
        if (fm && /^\s*hidden:\s*true\s*$/m.test(fm[1])) {
          hidden.add(entry.name.replace(/\.md$/, ''));
        }
      }
    }
  };
  walk(dir);
  return hidden;
}

const hiddenSlugs = collectHiddenSlugs('./src/content/blog');

export default defineConfig({
  site: 'https://pinglin.tw',
  adapter: vercel({
    imageService: true,
    edgeMiddleware: true,
    webAnalytics: {
      enabled: true,
    },
  }),
  integrations: [
    mermaid({
      theme: 'base',
      autoTheme: false,
      mermaidConfig: {
        themeVariables: {
          // Match Mermaid's `neutral` theme palette for nodes/edges, but
          // make every label/canvas background transparent so the chart
          // blends with the surrounding card tint instead of stacking
          // opaque pills on top of it.
          background: 'transparent',
          mainBkg: '#eceff1',
          secondBkg: '#e0e0e0',
          tertiaryColor: 'transparent',
          edgeLabelBackground: 'transparent',
          clusterBkg: 'transparent',
          noteBkgColor: 'transparent',
          primaryColor: '#eceff1',
          primaryTextColor: '#1f2937',
          primaryBorderColor: '#9ca3af',
          lineColor: '#6b7280',
          fontSize: '13px',
        },
        flowchart: {
          // Default wrapping width (~200 px) breaks longer edge labels into
          // narrow stacks. Give them more horizontal room before wrapping.
          wrappingWidth: 400,
          htmlLabels: true,
          // Tighter vertical rhythm so multi-rank charts don't get excessive
          // gaps between layers when an edge has a label.
          rankSpacing: 35,
          nodeSpacing: 40,
        },
      },
    }),
    preact(),
    tailwind(),
    sitemap({
      filter: (page) => ![...hiddenSlugs].some((slug) => page.includes(`/${slug}/`)),
    }),
  ],
  markdown: {
    remarkPlugins: [
      () => (tree) => {
        visit(tree, 'text', (node) => {
          // Remove line breaks between Chinese characters
          node.value = node.value.replace(/(\p{Script=Han})\s+(\p{Script=Han})/gu, '$1$2');
        });
      },
    ],
  },
  i18n: {
    defaultLocale: defaultLang,
    locales: supportedLanguages,
    routing: {
      prefixDefaultLocale: false,
    },
    fallback: {
      'zh-tw': defaultLang,
    },
  },
});

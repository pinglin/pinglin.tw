import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel';
import preact from '@astrojs/preact';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';
import { visit } from 'unist-util-visit';

import { languages, defaultLang } from './src/i18n/ui';

const supportedLanguages = Object.keys(languages);

export default defineConfig({
  site: 'https://pinglin.tw',
  adapter: vercel({
    imageService: true,
    edgeMiddleware: true,
    webAnalytics: {
      enabled: true,
    },
  }),
  integrations: [preact(), tailwind(), sitemap()],
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
  build: {
    sourcemap: true
  }
});

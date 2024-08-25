import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel/serverless';
import preact from '@astrojs/preact';
import tailwind from '@astrojs/tailwind';

import { languages, defaultLang } from './src/i18n/ui';

const supportedLanguages = Object.keys(languages);

export default defineConfig({
  site: 'https://pinglin.io',
  output: 'server',
  adapter: vercel({
    analytics: true,
    edgeMiddleware: true,
  }),
  integrations: [preact(), tailwind()],
  i18n: {
    defaultLocale: defaultLang,
    locales: supportedLanguages,
    routing: {
      prefixDefaultLocale: false,
    },
    fallback: {
      zh: defaultLang,
    },
  },
});

import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel';
import preact from '@astrojs/preact';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';
import mermaid from 'astro-mermaid';
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
    sitemap(),
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
  build: {
    sourcemap: true
  }
});

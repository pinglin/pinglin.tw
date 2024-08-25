import js from '@eslint/js';
import astroPlugin from 'eslint-plugin-astro';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';

export default [
  js.configs.recommended,
  ...astroPlugin.configs['flat/recommended'],
  {
    files: ['**/*.{js,mjs,cjs,jsx,ts,tsx,astro}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
      },
    },
    rules: {
      quotes: ['error', 'single'],
      indent: ['error', 2, { ignoredNodes: ['TemplateLiteral *'] }],
    },
  },
  {
    files: ['**/*.astro'],
    rules: {
      indent: 'off', // Turn off indent rule for Astro files
    },
  },
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    languageOptions: {
      parser: tsParser,
    },
  },
  {
    // Configuration for server-side files (e.g., API routes)
    files: ['src/pages/api/**/*.{js,ts}'],
    languageOptions: {
      globals: {
        Response: 'readonly',
      },
    },
  },
  {
    ignores: ['.astro/**', '.vercel/**', 'node_modules/**', 'dist/**'],
  },
];

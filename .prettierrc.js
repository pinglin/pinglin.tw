export default {
  plugins: ['prettier-plugin-astro'],
  overrides: [
    {
      files: '*.astro',
      options: {
        parser: 'astro',
        htmlWhitespaceSensitivity: 'ignore',
        astroAllowShorthand: false,
        printWidth: 100,
      },
    },
  ],
  semi: true,
  singleQuote: true,
  tabWidth: 2,
  trailingComma: 'all',
  printWidth: 80,
  proseWrap: 'always',
};

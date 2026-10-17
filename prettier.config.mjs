export default {
  semi: true,
  singleQuote: true,
  tabWidth: 2,
  plugins: [
    '@ianvs/prettier-plugin-sort-imports',
    'prettier-plugin-astro',
    'prettier-plugin-tailwindcss',
  ],
  importOrder: ['<THIRD_PARTY_MODULES>', '', '^@/(.*)$', '', '^[.]'],
  importOrderParserPlugins: ['typescript'],
  tailwindStylesheet: './src/styles/global.css',
  overrides: [
    {
      files: '*.astro',
      options: {
        parser: 'astro',
      },
    },
  ],
};

export default {
  semi: true,
  singleQuote: true,
  tabWidth: 2,
  plugins: ['@ianvs/prettier-plugin-sort-imports', 'prettier-plugin-astro'],
  importOrder: ['<THIRD_PARTY_MODULES>', '', '^@/(.*)$', '', '^[.]'],
  importOrderParserPlugins: ['typescript'],
  overrides: [
    {
      files: '*.astro',
      options: {
        parser: 'astro',
      },
    },
  ],
};

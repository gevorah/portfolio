/** @type {import("prettier").Config} */
export default {
  semi: true,
  singleQuote: true,
  tabWidth: 2,
  plugins: [
    '@ianvs/prettier-plugin-sort-imports',
    'prettier-plugin-astro',
    'prettier-plugin-tailwindcss',
  ],
  importOrder: [
    '^(react/(.*)$)|^(react$)',
    '<THIRD_PARTY_MODULES>',
    '',
    '^@/lib/(.*)$',
    '^@/components/(.*)$',
    '',
    '^[.]',
  ],
  importOrderParserPlugins: ['typescript', 'jsx', 'decorators-legacy'],
  overrides: [
    {
      files: '*.astro',
      options: {
        parser: 'astro',
      },
    },
  ],
  tailwindFunctions: ['cn', 'cva'],
};

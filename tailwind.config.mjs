import defaultTheme from 'tailwindcss/defaultTheme';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,md,mdx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono Variable', ...defaultTheme.fontFamily.mono]
      },
      colors: {
        primary: {
          hard: '#1d2021',
          DEFAULT: '#282828',
          soft: '#32302f',
          1: '#3c3836',
          2: '#665c54',
          3: '#7c6f64',
          4: '#928374'
        },
        secondary: {
          hard: '#f9f5d7',
          DEFAULT: '#fbf1c7',
          soft: '#f2e5bc',
          1: '#ebdbb2',
          2: '#d5c4a1',
          3: '#bdae93',
          4: '#a89984'
        },
        normal: {
          black: '#282828',
          red: '#cc241d',
          green: '#98971a',
          yellow: '#d79921',
          blue: '#458588',
          purple: '#b16286',
          aqua: '#689d6a',
          gray: '#a89984',
          orange: '#d65d0e'
        },
        bright: {
          black: '#928374',
          red: '#fb4934',
          green: '#b8bb26',
          yellow: '#fabd2f',
          blue: '#83a598',
          purple: '#d3869b',
          aqua: '#8ec07c',
          gray: '#928374',
          orange: '#fe8019'
        },
        dim: {
          black: '#32302f',
          red: '#9d0006',
          green: '#79740e',
          yellow: '#b57614',
          blue: '#076678',
          purple: '#8f3f71',
          aqua: '#427b58',
          gray: '#7c6f64',
          orange: '#af3a03'
        }
      }
    }
  },
  plugins: []
};


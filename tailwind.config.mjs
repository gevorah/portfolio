import defaultTheme from 'tailwindcss/defaultTheme';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,md,mdx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Space Grotesk Variable', ...defaultTheme.fontFamily.sans],
      },
      colors: {
        primary: '#AF97C8',
        secondary: '#30223F',
        accent: '#6009BE',
        foreground: '#ECE6F4',
        background: '#16022C'
      }
    }
  },
  plugins: []
};


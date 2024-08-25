import daisyui from 'daisyui';

export default {
  darkMode: ['selector', '[data-theme="night"]'],
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  daisyui: {
    themes: ['cmyk', 'night'],
  },
  plugins: [daisyui],
  theme: {
    extend: {
      fontFamily: {
        metrophobic: ['Metrophobic', 'sans-serif'],
      },
    },
  },
};

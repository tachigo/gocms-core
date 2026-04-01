/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  // 避免 Tailwind 与 ElementPlus 样式冲突
  corePlugins: {
    preflight: false,
  },
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--cms-color-primary)',
          light: 'var(--cms-color-primary-light)',
          dark: 'var(--cms-color-primary-dark)',
        },
        success: 'var(--cms-color-success)',
        warning: 'var(--cms-color-warning)',
        danger: 'var(--cms-color-danger)',
        info: 'var(--cms-color-info)',
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
      },
      boxShadow: {
        card: '0 1px 2px hsla(220,13%,13%,0.05)',
        dropdown: '0 4px 12px hsla(220,13%,13%,0.1)',
        modal: '0 8px 24px hsla(220,13%,13%,0.12)',
      },
    },
  },
  plugins: [],
}

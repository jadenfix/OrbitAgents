/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      container: {
        center: true,
        padding: {
          DEFAULT: '1rem',
          sm: '2rem',
          lg: '4rem',
          xl: '5rem',
          '2xl': '6rem',
        },
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: 'inherit',
            a: {
              color: 'inherit',
              textDecoration: 'underline',
              fontWeight: '500',
            },
            '[class~="lead"]': {
              color: 'inherit',
            },
            strong: {
              color: 'inherit',
              fontWeight: '600',
            },
            'ol[type="A"]': {
              '--tw-ordinal': 'upper-alpha',
            },
            'ol[type="a"]': {
              '--tw-ordinal': 'lower-alpha',
            },
            'ol[type="A" s]': {
              '--tw-ordinal': 'upper-alpha',
            },
            'ol[type="a" s]': {
              '--tw-ordinal': 'lower-alpha',
            },
            'ol[type="I"]': {
              '--tw-ordinal': 'upper-roman',
            },
            'ol[type="i"]': {
              '--tw-ordinal': 'lower-roman',
            },
            'ol[type="I" s]': {
              '--tw-ordinal': 'upper-roman',
            },
            'ol[type="i" s]': {
              '--tw-ordinal': 'lower-roman',
            },
            'ol[type="1"]': {
              '--tw-ordinal': 'decimal',
            },
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

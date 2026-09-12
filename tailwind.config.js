/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Outfit', 'sans-serif'],
      },
      colors: {
        fz: {
          black: '#0a0a0a',
          white: '#ffffff',
          gray: {
            100: '#f4f4f5',
            200: '#e4e4e7',
            300: '#d4d4d8',
            800: '#27272a',
            900: '#18181b',
          },
          red: {
            DEFAULT: '#e11d48',
            hover: '#be123c',
          }
        }
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.05)',
        'glass-dark': '0 4px 30px rgba(0, 0, 0, 0.2)',
      }
    }
  },
  plugins: [],
}

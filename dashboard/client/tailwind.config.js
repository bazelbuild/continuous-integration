module.exports = {
  mode: 'jit',
  purge: ['./pages/**/*.{js,ts,jsx,tsx}', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {
      colors: {
        blue: {
          'github': 'rgb(3, 102, 214)'
        }
      }
    },
  },
  variants: {
    extend: {},
  },
  plugins: [],
}

module.exports = {
  content: ['./pages/**/*.{js,ts,jsx,tsx}', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        blue: {
          'github': 'rgb(3, 102, 214)',
        },
        green: {
          'bazel': '#43a047',
          'bazel-light': '#76d275',
        }
      },

      zIndex: {
        'header': 1400,
        'popup': 1300,
      }
    },
  },
  plugins: [],
}

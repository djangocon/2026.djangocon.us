module.exports = {
  plugins: {
    'postcss-import': {},
    'postcss-simple-vars': {},
    'tailwindcss/nesting': {},
    tailwindcss: {},
    autoprefixer: {},
    ...(process.env.NODE_ENV === 'production' ? { cssnano: {} } : {})
  }
}
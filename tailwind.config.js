/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,md,liquid}"],
  safelist: [
    'border-t-primary',
    'border-t-orange',
    'border-orange',
    'border-dark-blue',
    'border-yellow',
    'bg-yellow',
    'shadow-avatar-orange',
    'shadow-avatar-dark-blue',
    'shadow-avatar-yellow',
  ],
  theme: {
    extend: {
      screens: {
        'xs': '420px'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        tanker: ['Tanker-Regular', 'Bebas Neue', 'sans-serif'],
      },
      colors: {
        'ocean-blue': {
          '200': '#CBD7FF',
          '300': '#9CB2FF',
          DEFAULT: '#9CB2FF',
          '400': '#7B97F5',
          '500': '#546CE3',
        },
        'dark-blue': '#102775',
        'yellow': '#FFBC5E',
        'orange': '#FF6752',
        'primary': '#9CB2FF',
        'secondary': '#BBBDC1',
        'background': {
          DEFAULT: '#F3F5FC',
          'dark': '#ECEFFC'
        },
        'stroke': '#E6EBF2',
        'black': {
          '50': '#F5F5F7',
          '100': '#E9E9EC',
          '200': '#D0D0D5',
          '300': '#ACACB4',
          '400': '#87878F',
          '500': '#63636A',
          '600': '#4A4A51',
          '700': '#363639',
          '800': '#2C2C32',
          '900': '#222228',
          DEFAULT: '#222228',
          '950': '#141418',
        },
        'social': {
          'bluesky': '#1185fe',
          'facebook': '#0866ff',
          'instagram': '#ff0069',
          'linkedin': '#2d64bc',
          'twitter': '#4a99e9',
          'github': '#7041c0',
          'mastodon': '#6364FF',
        }
      },
      fontSize: {
        '5xl': ['3rem', 1.15],
        'h1': ['3rem', 1.25],
        'h2': ['2.5rem', 1.15],
        'h3': ['1.5rem', 1.15],
        'h4': ['1.25rem', 1.25],
      },
      boxShadow: {
        'button': '8px -8px 0px 0px theme("colors.dark-blue")',
        'button-hover': '4px -4px 0px 0px theme("colors.dark-blue")',
        'button-active': '6px -6px 0px 0px theme("colors.dark-blue")',
        'avatar-orange': '5px -2px 0px 0px theme("colors.orange")',
        'avatar-dark-blue': '5px -2px 0px 0px theme("colors.dark-blue")',
        'avatar-yellow': '5px -2px 0px 0px theme("colors.yellow")',
      },
    },
  },
  plugins: [
    require('@tailwindcss/container-queries'),
    require('@tailwindcss/typography')
  ],
}

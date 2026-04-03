/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,md,liquid}"],
  safelist: [
    'border-t-primary',
    'border-t-orange'
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
          '50': '#FAFCFF',
          '100': '#E3EAFF',
          '200': '#CBD7FF',
          '300': '#9CB2FF',
          DEFAULT: '#9CB2FF',
          '400': '#7B97F5',
          '500': '#546CE3',
          '600': '#3B51CC',
          '700': '#2838A8',
          '800': '#1A2480',
          '900': '#0F165A',
          '950': '#090E3B',
        },
        'dark-blue': {
          '50': '#EEF1FC',
          '100': '#D4DCFA',
          '200': '#A9B9F7',
          '300': '#7D96F2',
          '400': '#5373E8',
          '500': '#3052D4',
          '600': '#2040B0',
          '700': '#172E8C',
          '800': '#102775',
          DEFAULT: '#102775',
          '900': '#091752',
          '950': '#050D33',
        },
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
        },
        'yellow': '#FFBC5E',
        'orange': '#FF6752',
        'primary': '#9CB2FF',
        'secondary': '#BBBDC1',
        'background': '#F3F5FC',
        'background-dark': '#ECEFFC',
        'stroke': '#E6EBF2'
      },
      fontSize: {
        '5xl': ['3rem', 1.1]
      },
      boxShadow: {
        'button': '8px -8px 0px 0px theme("colors.dark-blue.DEFAULT")',
        'button-hover': '4px -4px 0px 0px theme("colors.dark-blue.DEFAULT")',
        'button-active': '6px -6px 0px 0px theme("colors.dark-blue.DEFAULT")',
      },
    },
  },
  plugins: [
    require('@tailwindcss/container-queries'),
    require('@tailwindcss/typography')
  ],
}

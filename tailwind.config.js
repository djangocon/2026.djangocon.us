/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,md,liquid}"],
  safelist: [
    'border-t-ocean-blue',
    'border-t-ocean-blue',
    'border-t-ocean-blue',
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
        'orange': {
          '50': '#FFF2F0',
          '100': '#FFDDD9',
          '200': '#FFB8B0',
          '300': '#FF9285',
          '400': '#FF6752',
          DEFAULT: '#FF6752',
          '500': '#F03D29',
          '600': '#CC2718',
          '700': '#A31E12',
          '800': '#7A140C',
          '900': '#520D07',
          '950': '#330804',
        },
        'yellow': {
          '50': '#FFFAEF',
          '100': '#FFF0CC',
          '200': '#FFE0A0',
          '300': '#FFBC5E',
          DEFAULT: '#FFBC5E',
          '400': '#FFA020',
          '500': '#E87D00',
          '600': '#CC6C00',
          '700': '#A35500',
          '800': '#7A3F00',
          '900': '#502800',
          '950': '#331900',
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
        'secondary': '#BBBDC1'
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

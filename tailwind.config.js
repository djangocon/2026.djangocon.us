/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,md,liquid}"],
  safelist: [
    'border-t-green',
    'border-t-teal',
    'border-t-cyan',
    'border-t-orange'
  ],
  theme: {
    extend: {
      screens: {
        'xs': '420px'
      },
      fontFamily: {
        sans: ['Figtree', 'sans-serif'],
      },
      colors: {
        'teal': {
          '50': '#E5F4F7',
          '100': '#CCE9EF',
          '200': '#82C0CD',
          '300': '#4E9FB2',
          DEFAULT: '#006676',
          '400': '#006676',
          '500': '#045260',
          'dark': '#033A43', // Original dark teal color
          '600': '#033A43', // Original dark teal color
          '700': '#022931',
          '800': '#011F25',
          '900': '#01151A',
          '950': '#000D10',
        },
        'cyan': {
          '50': '#EBF7F6',
          '100': '#DFF2F0',
          '200': '#C8E9E5',
          '300': '#B0DFDA',
          '400': '#99D6CF',
          '500': '#82D0C8',
          DEFAULT: '#82D0C8',
          '700': '#40B0A4',
          '800': '#348B81',
          '900': '#266660',
          '950': '#1D4F4A',
        },
        'green': {
          '50': '#E3EBCF',
          '100': '#D8E4BE',
          '200': '#C2D59D',
          '300': '#ACC77B',
          '400': '#96B85A',
          '500': '#96B85A',
          DEFAULT: '#96B85A',
          '700': '#53682C',
          '800': '#3C4B20',
          '900': '#252E14',
          '950': '#19200E',
        },
        'orange': {
          '50': '#FCF0D7',
          '100': '#FAE8C3',
          '200': '#F8D99B',
          '300': '#F6CA73',
          '400': '#F4BC4B',
          '500': '#F3B12E',
          DEFAULT: '#F3B12E',
          '700': '#E39A0A',
          '800': '#956507',
          '900': '#6F4B05',
          '950': '#4C3404',
        },
        'pink': {
          '50': '#F6E4EF',
          '100': '#EFD0E3',
          '200': '#E6B6D3',
          '300': '#DE9CC3',
          '400': '#D682B3',
          '500': '#DA6A9E',
          DEFAULT: '#DA6A9E',
          '700': '#C04B81',
          '800': '#A03A69',
          '900': '#802E54',
          '950': '#5A1F3B',
        },
        'gold': {
          '50': '#FEF8E7',
          '100': '#FDF1CF',
          '200': '#FCE8B3',
          '300': '#FBDE97',
          '400': '#FAD57B',
          '500': '#FCD882',
          DEFAULT: '#FCD882',
          '700': '#E5B84B',
          '800': '#C99A2F',
          '900': '#A47D1E',
          '950': '#7A5E16',
        },
        'cream': {
          "50": "#FEFDFA",
          "100": "#FEFCF6",
          "200": "#FDFAF1",
          "300": "#FCF7E8",
          "400": "#FCF5E3",
          "500": "#FBF2DB",
          DEFAULT: '#FBF2DB',
          "600": "#F2D488",
          "700": "#E8B430",
          "800": "#AA7F13",
          "900": "#533E09",
          "950": "#291F05",
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
        '5xl': ['3rem', 1.1]
      },
    },
  },
  plugins: [
    require('@tailwindcss/container-queries'),
    require('@tailwindcss/typography')
  ],
}

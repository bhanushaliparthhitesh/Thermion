/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#F7F9FC',
        card: '#FFFFFF',
        border: {
          DEFAULT: '#E4E7EC',
          strong: '#D0D5DD',
        },
        ink: {
          DEFAULT: '#101828',
          soft: '#475467',
          faint: '#98A2B3',
        },
        primary: {
          50: '#EAF1FC',
          100: '#CFE1F8',
          500: '#2C6FDB',
          600: '#1E56C4',
          700: '#163F94',
        },
        cooling: {
          50: '#E3F6F4',
          500: '#12A69A',
          600: '#0F9B8E',
          700: '#0B7A70',
        },
        safe: {
          50: '#E7F6EC',
          500: '#1B9E4C',
          600: '#15803D',
          700: '#106430',
        },
        warn: {
          50: '#FDF1E0',
          500: '#D0820F',
          600: '#B45309',
          700: '#8F4207',
        },
        critical: {
          50: '#FBE9E9',
          500: '#D92D2D',
          600: '#B91C1C',
          700: '#921616',
        },
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(16, 24, 40, 0.04), 0 1px 3px rgba(16, 24, 40, 0.06)',
      },
      borderRadius: {
        card: '10px',
      },
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        xuan: {
          dark: '#0A0D12',
          DEFAULT: '#0C1113',
          panel: '#151C20',
          card: '#121721',
          border: 'rgba(212, 175, 55, 0.16)',
          hover: 'rgba(212, 175, 55, 0.35)',
        },
        gold: {
          DEFAULT: '#D4AF37',
          light: '#F5D46E',
          bright: '#F7DF94',
          dark: '#A68524',
          muted: 'rgba(212, 175, 55, 0.25)',
        },
        cinnabar: {
          DEFAULT: '#C83C23',
          light: '#EE5C42',
          dark: '#9E2813',
          muted: 'rgba(200, 60, 35, 0.2)',
        },
        celadon: {
          DEFAULT: '#3E8E7E',
          light: '#62C0AC',
          bright: '#85D3C3',
          muted: 'rgba(62, 142, 126, 0.2)',
        },
        paper: {
          bg: '#F3EBDC',
          light: '#FAF6EE',
          ink: '#2B2520',
          border: '#D3C3A8',
          grid: 'rgba(139, 105, 60, 0.25)',
        }
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', '"Source Han Serif SC"', '"SimSun"', '"STSong"', 'serif'],
        sans: ['"PingFang SC"', '"Microsoft YaHei"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'gold-glow': '0 0 20px rgba(212, 175, 55, 0.25)',
        'cinnabar-glow': '0 0 20px rgba(200, 60, 35, 0.3)',
        'celadon-glow': '0 0 20px rgba(62, 142, 126, 0.3)',
        'card': '0 8px 32px 0 rgba(0, 0, 0, 0.5)',
      },
      animation: {
        'scan': 'scan 4s cubic-bezier(0.4, 0, 0.2, 1) infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        scan: {
          '0%, 100%': { top: '0%' },
          '50%': { top: '96%' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' },
        }
      }
    },
  },
  plugins: [],
}

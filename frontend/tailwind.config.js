/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        surface: {
          0: '#FDFDFC',
          1: '#F6F6F4',
          2: '#EEEEEC',
          3: '#E3E3E0',
          inv: '#1A1A19',
        },
        ink: {
          DEFAULT: '#1D1D1B',
          muted: '#6B6B68',
          faint: '#A1A19E',
          inverse: '#F6F6F4',
        },
        line: {
          DEFAULT: '#E3E3E0',
          strong: '#CDCDCA',
        },
        accent: {
          DEFAULT: '#5746AF',
          light: '#EDE9FE',
          hover: '#4A3B9B',
          text: '#5746AF',
        },
        ok: {
          DEFAULT: '#2D8C4E',
          light: '#E8F5ED',
        },
        warn: {
          DEFAULT: '#B8860B',
          light: '#FEF9E7',
        },
        bad: {
          DEFAULT: '#C4352A',
          light: '#FDF0EF',
        },
        dark: {
          0: '#111110',
          1: '#191918',
          2: '#222221',
          3: '#2E2E2C',
          4: '#3A3A37',
          ink: '#EDEDEB',
          muted: '#A1A19E',
          faint: '#6B6B68',
          line: '#2E2E2C',
          'line-strong': '#3A3A37',
        },
      },
      borderRadius: {
        '2xl': '16px',
        '3xl': '20px',
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)',
        'modal': '0 16px 48px rgba(0,0,0,0.12)',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'count-up': 'fadeIn 0.6s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(-12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
      },
    },
  },
  plugins: [],
}

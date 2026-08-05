/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ocean: {
          900: '#030712',
          800: '#0b1329',
          700: '#111e38',
          600: '#1a2e54',
          500: '#254478',
        },
        cyan: {
          400: '#38bdf8',
          500: '#06b6d4',
          600: '#0891b2',
        },
        hazard: {
          safe: '#10b981',
          watch: '#f59e0b',
          warning: '#f97316',
          severe: '#ef4444',
        }
      },
      animation: {
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
        'radar-sweep': 'radar 4s linear infinite',
      },
      keyframes: {
        radar: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        }
      }
    },
  },
  plugins: [],
}

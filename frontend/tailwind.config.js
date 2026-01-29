/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        // Existing primary colors (indigo/blue)
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        // Existing secondary colors (green)
        secondary: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
        },
        // Wellness-focused color extensions
        wellness: {
          // Light theme colors (eye-friendly off-whites)
          light: {
            bg: '#fafbfc',       // Very light blue-gray
            card: '#f8fafc',     // Off-white with slight blue tint
            elevated: '#f1f5f9', // Slightly darker off-white
            text: '#0f172a',     // Dark slate
            textSecondary: '#475569', // Medium slate
            textMuted: '#64748b', // Light slate
            border: '#e2e8f0',   // Light slate border
          },
          // Dark theme colors
          dark: {
            bg: '#0f172a',       // slate-900
            card: '#1e293b',     // slate-800
            elevated: '#334155', // slate-700
            text: '#f1f5f9',     // slate-100
            textSecondary: '#cbd5e1', // slate-300
            textMuted: '#94a3b8', // slate-400
            border: '#475569',   // slate-600
          }
        }
      }
    },
  },
  plugins: [],
}
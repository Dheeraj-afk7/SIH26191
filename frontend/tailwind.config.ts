import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0A1428',
          900: '#0F2044', // Primary sidebar background
          850: '#132854',
          800: '#162F65',
          700: '#1E3A8A',
          600: '#2563EB',
          500: '#3B82F6',
          400: '#60A5FA',
        },
        official: {
          blue: '#1D4ED8',    // Official India Blue
          hover: '#1E40AF',
          light: '#EFF6FF',
          border: '#BFDBFE',
        },
        workspace: {
          bg: '#F1F5F9',     // Slate-100 neutral workspace
          card: '#FFFFFF',
          hover: '#F8FAFC',
          border: '#E2E8F0',
          subtle: '#CBD5E1',
        },
        tier: {
          t1: {
            bg: '#FEF2F2',
            text: '#991B1B',
            border: '#FCA5A5',
            badge: '#DC2626',
          },
          t2: {
            bg: '#FFFBEB',
            text: '#92400E',
            border: '#FCD34D',
            badge: '#D97706',
          },
          t3: {
            bg: '#EFF6FF',
            text: '#1E40AF',
            border: '#93C5FD',
            badge: '#2563EB',
          },
          beyond: {
            bg: '#F8FAFC',
            text: '#334155',
            border: '#CBD5E1',
            badge: '#64748B',
          }
        },
        hazard: {
          redzone: '#DC2626',
          redzoneFill: 'rgba(220, 38, 38, 0.25)',
          candidate: '#D97706',
          candidateFill: 'rgba(217, 119, 6, 0.15)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(15, 23, 42, 0.08), 0 1px 2px -1px rgba(15, 23, 42, 0.04)',
        'card-hover': '0 4px 6px -1px rgba(15, 23, 42, 0.12), 0 2px 4px -2px rgba(15, 23, 42, 0.08)',
        nav: '2px 0 8px 0 rgba(10, 20, 40, 0.15)',
      }
    },
  },
  plugins: [],
};

export default config;

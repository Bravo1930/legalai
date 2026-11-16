import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ["'EB Garamond'", "Georgia", "serif"],
        sans: ["'Lato'", "system-ui", "sans-serif"],
      },
      transitionTimingFunction: {
        'apple-spring': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'apple-press': 'cubic-bezier(0.2, 0, 0, 1)',
      },
      colors: {
        legal: {
          50: "#f8f9fa",
          100: "#f1f3f5",
          200: "#e9ecef",
          300: "#dee2e6",
          400: "#ced4da",
          500: "#adb5bd",
          600: "#6c757d",
          700: "#495057",
          800: "#343a40",
          900: "#212529",
          navy: "#0f172a",
          gold: "#c59b27",
          border: "#e2e8f0"
        }
      }
    },
  },
  plugins: [],
};
export default config;

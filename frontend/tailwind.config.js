/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          50: "#f5f7fa",
          100: "#e4e9f0",
          200: "#c6d0dd",
          300: "#8fa2b8",
          400: "#5e758f",
          500: "#415876",
          600: "#2e415a",
          700: "#1f2f45",
          800: "#14203a",
          900: "#0b162c",
        },
        accent: {
          DEFAULT: "#ff6b35",
          soft: "#ffe1d4",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Menlo", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};

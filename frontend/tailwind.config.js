/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  theme: {
    extend: {
      colors: {
        ink: "#172033",
        brand: "#1D4ED8",
        surface: "#F8FAFC",
        line: "#E2E8F0",
        muted: "#64748B",
      },

      boxShadow: {
        soft: "0 1px 3px rgba(15, 23, 42, 0.08)",
      },
    },
  },

  plugins: [],
};
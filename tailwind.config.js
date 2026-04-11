/** Purged Tailwind build for Django templates + static JS. Run: npm run build:css */
module.exports = {
  content: ["./templates/**/*.html", "./static/**/*.js"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#0d9488", dark: "#0f766e", light: "#ccfbf1" },
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
      },
    },
  },
  plugins: [],
};

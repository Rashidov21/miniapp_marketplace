/** Purged Tailwind build for Django templates + static JS. Run: npm run build:css */
module.exports = {
  content: ["./templates/**/*.html", "./static/**/*.js"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#0d9488", dark: "#0f766e", light: "#ccfbf1" },
        /** Semantic UI (8px grid bilan birga ishlatiladi) */
        ui: {
          primary: "#0d9488",
          "primary-dark": "#0f766e",
          success: "#059669",
          "success-soft": "#d1fae5",
          error: "#dc2626",
          "error-soft": "#ffe4e6",
          warning: "#d97706",
        },
      },
      spacing: {
        /** 8px bazali qo‘shimcha tokenlar (1 = 4px TW default) */
        "ui-1": "0.5rem",
        "ui-2": "1rem",
        "ui-3": "1.5rem",
        "ui-4": "2rem",
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        "ui-card": "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
      },
    },
  },
  plugins: [],
};

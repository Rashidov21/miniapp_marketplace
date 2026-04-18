/** Purged Tailwind build for Django templates + static JS. Run: npm run build:css */
/** Stitch “Digital Curator” palette — staticfiles/stitch_uz_store_express/ */
module.exports = {
  content: ["./templates/**/*.html", "./static/**/*.js"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#00685f", dark: "#005049", light: "#89f5e7" },
        primary: "#00685f",
        "primary-container": "#008378",
        "on-primary": "#ffffff",
        "on-surface": "#0b1c30",
        "on-surface-variant": "#3d4947",
        surface: "#f8f9ff",
        "surface-bright": "#f8f9ff",
        "surface-dim": "#cbdbf5",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#eff4ff",
        "surface-container": "#e5eeff",
        "surface-container-high": "#dce9ff",
        "surface-container-highest": "#d3e4fe",
        "surface-variant": "#d3e4fe",
        background: "#f8f9ff",
        secondary: "#3f6560",
        "secondary-container": "#c2ebe3",
        outline: "#6d7a77",
        "outline-variant": "#bcc9c6",
        error: "#ba1a1a",
        "error-container": "#ffdad6",
        /** Semantic UI (legacy + badges) */
        ui: {
          primary: "#00685f",
          "primary-dark": "#005049",
          success: "#00685f",
          "success-soft": "#eff4ff",
          error: "#ba1a1a",
          "error-soft": "#ffdad6",
          warning: "#924628",
        },
      },
      fontFamily: {
        headline: ['"Plus Jakarta Sans"', "system-ui", "sans-serif"],
        body: ['Inter', "system-ui", "sans-serif"],
      },
      spacing: {
        "ui-1": "0.5rem",
        "ui-2": "1rem",
        "ui-3": "1.5rem",
        "ui-4": "2rem",
      },
      boxShadow: {
        card: "0 24px 48px -12px rgba(11, 28, 48, 0.08)",
        "ui-card": "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        editorial: "0 24px 48px -12px rgba(11, 28, 48, 0.08)",
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.jsx", "./components/**/*.jsx"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
      colors: { slate: { 850: "#151e2e", 950: "#0a0f18" } },
      borderRadius: { "3xl": "24px", "4xl": "32px", "5xl": "48px" },
      keyframes: {
        float: { "0%, 100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-8px)" } },
        shimmer: { "100%": { transform: "translateX(100%)" } },
        "slide-up": { from: { opacity: 0, transform: "translateY(16px)" }, to: { opacity: 1, transform: "none" } },
        "pop-in": { from: { opacity: 0, transform: "scale(0.94)" }, to: { opacity: 1, transform: "none" } },
        "sheet-up": { from: { transform: "translateY(100%)" }, to: { transform: "none" } },
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        shimmer: "shimmer 2s infinite",
        "slide-up": "slide-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) both",
        "pop-in": "pop-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both",
        "sheet-up": "sheet-up 0.35s cubic-bezier(0.16, 1, 0.3, 1) both",
      },
    },
  },
  plugins: [],
};

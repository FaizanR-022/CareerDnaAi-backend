import { theme } from "./src/constants/theme.js";

/** @type {import('tailwindcss').Config} */
const config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: theme.colors,
      borderRadius: theme.borderRadius,
      spacing: theme.spacing,
      fontFamily: theme.fontFamily,
      fontSize: theme.fontSize,
    },
  },
  plugins: [],
};

export default config;

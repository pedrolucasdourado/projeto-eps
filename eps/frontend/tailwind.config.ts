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
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      colors: {
        shell: {
          bg: "#0b0d11",
          surface: "#131821",
          sidebar: "#0f141c",
          sidebarHover: "#1a2230",
          border: "#2a3342",
          text: "#d8dee9",
          muted: "#8e98a8",
          accent: "#b38b3d",
          accentBlue: "#1f3b68",
        },
      },
    },
  },
  plugins: [],
};

export default config;

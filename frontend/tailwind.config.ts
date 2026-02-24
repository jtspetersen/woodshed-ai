import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        amber: {
          50: "#FFF8F0",
          100: "#FEECD2",
          200: "#FDD9A5",
          300: "#FCBF6A",
          400: "#F5A623",
          500: "#D4890A",
          600: "#A66A08",
        },
        bark: {
          50: "#F7F4F1",
          100: "#EDE8E3",
          200: "#DDD5CE",
          300: "#C4B9AF",
          400: "#A89A8D",
          500: "#87776A",
          600: "#6B5B4B",
          700: "#524538",
          800: "#3D3229",
          900: "#2A211B",
          950: "#1A1310",
        },
        rust: {
          300: "#F08A66",
          400: "#E06D45",
          500: "#C75C3A",
        },
        sage: {
          300: "#99C4A5",
          400: "#7AAB87",
          500: "#5E8C6A",
        },
      },
      fontFamily: {
        display: ["var(--font-nunito)", "Nunito", "sans-serif"],
        body: ["var(--font-nunito-sans)", "Nunito Sans", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "monospace"],
      },
      borderRadius: {
        sm: "6px",
        md: "10px",
        lg: "16px",
        xl: "24px",
      },
      boxShadow: {
        sm: "0 1px 3px rgba(0,0,0,0.25)",
        md: "0 4px 12px rgba(0,0,0,0.3)",
        lg: "0 8px 30px rgba(0,0,0,0.35)",
        glow: "0 0 20px rgba(245,166,35,0.15)",
      },
      transitionTimingFunction: {
        "ease-out": "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
      },
      transitionDuration: {
        fast: "150ms",
        normal: "250ms",
        slow: "400ms",
      },
    },
  },
  plugins: [],
};
export default config;

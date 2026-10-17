import type { Config } from "tailwindcss";
const c = (v: string) => `rgb(var(--${v}) / <alpha-value>)`;
export default {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: { extend: {
    colors: { bg: c("bg"), fg: c("fg"), muted: c("muted"), line: c("line"), soft: c("soft"), accent: c("accent"),
      onaccent: c("onaccent"), brand: c("brand"), ok: c("ok"), warn: c("warn"), bad: c("bad") },
    fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"] },
  } },
} satisfies Config;

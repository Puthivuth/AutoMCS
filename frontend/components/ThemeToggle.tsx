"use client";
import { useEffect, useState } from "react";
export default function ThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => setDark(document.documentElement.classList.contains("dark")), []);
  const toggle = () => {
    const next = !dark; setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try { localStorage.setItem("automcs-theme", next ? "dark" : "light"); } catch {}
  };
  return (<button onClick={toggle} aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
    className="rounded-lg border border-line px-3 py-1.5 text-sm font-medium hover:bg-soft">{dark ? "☀ Light" : "☾ Dark"}</button>);
}

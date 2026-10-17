"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Brand from "@/components/Brand";
import ThemeToggle from "@/components/ThemeToggle";

const links = [["/", "Home"], ["/about", "About"], ["/contact", "Contact"], ["/login", "Login"]];
export default function PublicLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (<div className="flex min-h-screen flex-col">
    <header className="sticky top-0 z-10 border-b border-line bg-bg/90 backdrop-blur">
      <nav className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-3">
        <Brand />
        <div className="flex items-center gap-1">
          {links.map(([h, t]) => (<Link key={h} href={h} className={`rounded-lg px-3 py-1.5 text-sm font-medium ${path === h ? (h === "/login" ? "bg-accent text-onaccent" : "bg-soft") : h === "/login" ? "bg-accent text-onaccent" : "text-muted hover:text-fg"}`}>{t}</Link>))}
          <ThemeToggle />
        </div>
      </nav>
    </header>
    <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-10">{children}</main>
    <footer className="border-t border-line py-6 text-center text-sm text-muted">AutoMCS · decimal table extraction for research</footer>
  </div>);
}

"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import Brand from "@/components/Brand";
import ThemeToggle from "@/components/ThemeToggle";
import { Button, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { useWs, WorkspaceProvider } from "@/lib/workspace";

const nav = [["/dashboard", "Dashboard"], ["/projects", "Projects"], ["/data", "Data & AI Prediction"], ["/review", "Review queue"], ["/evaluation", "Evaluation"], ["/export", "Export dataset"], ["/training", "Training"], ["/settings", "Settings"]];

function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname(); const router = useRouter(); const { projects, pid, setPid } = useWs();
  const logout = async () => { try { await api("/auth/logout/", { method: "POST" }); } finally { router.replace("/"); } };
  return (<div className="min-h-screen">
    <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-line bg-bg px-4 py-2.5">
      <Brand />
      <div className="flex items-center gap-2">
        <Select aria-label="Project" className="!w-44" value={pid ?? ""} onChange={(e: any) => setPid(Number(e.target.value))}>
          {projects.length === 0 && <option value="">No projects</option>}{projects.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}</Select>
        <ThemeToggle /><Button onClick={logout}>Logout</Button></div>
    </header>
    <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 md:grid-cols-[210px_1fr]">
      <nav className="flex gap-1 overflow-x-auto md:sticky md:top-20 md:flex-col md:self-start">
        {nav.map(([h, t]) => <Link key={h} href={h} className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium ${path.startsWith(h) || (h === "/data" && path.startsWith("/verify")) ? "bg-soft text-fg" : "text-muted hover:bg-soft hover:text-fg"}`}>{t}</Link>)}
      </nav>
      <section className="min-w-0">{children}</section>
    </div></div>);
}
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <WorkspaceProvider><Shell>{children}</Shell></WorkspaceProvider>;
}

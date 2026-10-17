"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "./api";

const Ctx = createContext<any>(null);
export const useWs = () => useContext(Ctx);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [pid, setPidState] = useState<number | null>(null);
  const load = useCallback(async () => {
    try {
      const [u, p] = await Promise.all([api("/auth/me/"), api("/projects/")]);
      setUser(u); setProjects(p);
      let saved: number | null = null;
      try { saved = Number(localStorage.getItem("automcs-project")) || null; } catch {}
      setPidState((cur) => (cur && p.some((x: any) => x.id === cur) ? cur : p.some((x: any) => x.id === saved) ? saved : p[0]?.id ?? null));
    } catch { router.replace("/login"); }
  }, [router]);
  useEffect(() => { load(); }, [load]);
  const setPid = (id: number) => { setPidState(id); try { localStorage.setItem("automcs-project", String(id)); } catch {} };
  if (!user) return <div className="grid min-h-screen place-items-center text-muted">Loading workspace…</div>;
  return <Ctx.Provider value={{ user, projects, pid, setPid, reload: load, project: projects.find((p) => p.id === pid) }}>{children}</Ctx.Provider>;
}

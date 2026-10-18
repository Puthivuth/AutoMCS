"use client";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui";
export default function About() {
  const [cfg, setCfg] = useState<any>({});
  useEffect(() => { fetch("/api/public/config/").then((r) => r.json()).then(setCfg).catch(() => {}); }, []);
  const pending = <span className="text-muted">To be confirmed</span>;
  const blocks = [["Background and motivation", "Building decimal-table datasets by hand is slow and error-prone. AutoMCS pairs AI extraction with human verification."],
    ["Methodology", "Import, AI extraction, two-decimal normalization, human review, evaluation against verified labels, and versioned export."],
    ["Expected contributions", "A reproducible, verified dataset pipeline and a benchmark of cloud versus local extraction."],
    ["Technologies", "Next.js, React, TypeScript, Tailwind, Django REST Framework, PostgreSQL, Celery, and Gemini API with multi-key auto-failover."]];
  return (<><h1 className="text-3xl font-semibold tracking-tight">About AutoMCS</h1>
    <div className="mt-6 grid gap-4 sm:grid-cols-2">{blocks.map(([t, d]) => <Card key={t}><h2 className="font-semibold">{t}</h2><p className="mt-1 text-sm text-muted">{d}</p></Card>)}
      <Card><h2 className="font-semibold">Researcher</h2><p className="mt-1 text-sm">Puthivuth Chhoeun</p>
        <p className="mt-2 text-sm">Supervisor: {cfg.supervisor || pending}</p><p className="text-sm">Institution: {cfg.institution || pending}</p></Card></div></>);
}

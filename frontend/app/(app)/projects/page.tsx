"use client";
import Link from "next/link";
import { useState } from "react";
import { api, msg } from "@/lib/api";
import { useWs } from "@/lib/workspace";
import { Badge, Button, Card, Input, Notice, PageHeader } from "@/components/ui";
export default function Projects() {
  const { projects, pid, setPid, reload } = useWs(); const [name, setName] = useState(""); const [err, setErr] = useState("");
  const run = async (fn: () => Promise<any>) => { setErr(""); try { await fn(); await reload(); } catch (e) { setErr(msg(e)); } };
  return (<><PageHeader title="Projects" />
    <Card><form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (name.trim()) run(async () => { const p = await api("/projects/", { json: { name: name.trim() } }); setName(""); setPid(p.id); }); }}>
      <Input placeholder="New project name" value={name} onChange={(e: any) => setName(e.target.value)} /><Button variant="primary">Create</Button></form></Card>
    {err && <div className="mt-3"><Notice tone="bad">{err}</Notice></div>}
    <div className="mt-4 grid gap-3 md:grid-cols-2">{projects.map((p: any) => (<Card key={p.id}>
      <div className="flex items-center justify-between"><h2 className="font-semibold">{p.name}</h2>{p.id === pid && <Badge tone="info">Selected</Badge>}</div>
      <p className="mt-1 text-xs text-muted">Created {new Date(p.created_at).toLocaleDateString()}. Documents, labels and exports are kept separate per project.</p>
      <div className="mt-3 flex gap-2"><Button size="sm" onClick={() => setPid(p.id)}>Select</Button><Link className="inline-flex items-center justify-center rounded-lg bg-accent px-2.5 py-1 text-xs font-medium text-onaccent" href="/data">Open data</Link>
        <Button size="sm" onClick={() => { const n = prompt("Rename project", p.name); if (n?.trim()) run(() => api(`/projects/${p.id}/`, { method: "PATCH", json: { name: n.trim() } })); }}>Rename</Button>
        <Button size="sm" variant="danger" onClick={() => { if (confirm("Archive this project? Data is kept.")) run(() => api(`/projects/${p.id}/`, { method: "DELETE" })); }}>Archive</Button></div></Card>))}</div></>);
}

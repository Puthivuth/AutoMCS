"use client";
import { useCallback, useEffect, useState } from "react";
import { api, msg } from "@/lib/api";
import { useWs } from "@/lib/workspace";
import { Badge, Button, Card, Notice, PageHeader, statusTone } from "@/components/ui";
export default function Export() {
  const { pid } = useWs(); const [jobs, setJobs] = useState<any[]>([]); const [o, setO] = useState({ allow_partial: false, include_history: false, jsonl: false }); const [err, setErr] = useState("");
  const load = useCallback(() => { if (pid) api(`/projects/${pid}/exports/`).then(setJobs).catch((e) => setErr(msg(e))); }, [pid]);
  useEffect(load, [load]);
  useEffect(() => { if (!jobs.some((j) => ["queued", "running"].includes(j.status))) return; const t = setInterval(load, 2500); return () => clearInterval(t); }, [jobs, load]);
  const create = async () => { setErr(""); try { await api(`/projects/${pid}/exports/`, { json: o }); load(); } catch (e) { setErr(msg(e)); } };
  const box = (k: keyof typeof o, t: string) => <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={o[k]} onChange={(e) => setO({ ...o, [k]: e.target.checked })} />{t}</label>;
  return (<><PageHeader title="Export dataset" />
    <Card><p className="text-sm text-muted">ZIP layout: <code>image_pdf/</code> originals, <code>groundtruth/</code> JSON and CSV per document, plus <code>manifest.json</code>. Only approved values are exported, as two-decimal strings.</p>
      <div className="mt-3 space-y-2">{box("jsonl", "Also write groundtruth.jsonl")}{box("include_history", "Include correction history")}{box("allow_partial", "Include partly approved documents (unapproved cells are listed in the JSON)")}</div>
      <Button variant="primary" className="mt-4" onClick={create}>Create export</Button></Card>
    {err && <div className="mt-3"><Notice tone="bad">{err}</Notice></div>}
    <div className="mt-4 space-y-2">{jobs.map((j) => <Card key={j.id} className="flex flex-wrap items-center justify-between gap-2 text-sm"><div><b>Export #{j.id}</b> <span className="text-muted">{new Date(j.created_at).toLocaleString()}</span>
      {j.summary?.included != null && <span className="text-muted"> · {j.summary.included} document(s), {j.summary.skipped.length} skipped</span>}{j.error && <span className="text-bad"> · {j.error}</span>}</div>
      <div className="flex items-center gap-2"><Badge tone={statusTone(j.status)}>{j.status}</Badge>{j.status === "done" && <a download={`automcs_dataset_${j.id}.zip`} className="rounded-lg bg-accent px-3 py-1 text-xs font-medium text-onaccent" href={`/api/exports/${j.id}/download/`}>Download ZIP</a>}{j.status === "failed" && <span className="text-bad">Export failed</span>}</div></Card>)}</div></>);
}

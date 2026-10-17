"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useWs } from "@/lib/workspace";
import { Card, Notice, PageHeader, Stat } from "@/components/ui";
const L: any = { documents: "Documents", images: "Images", pdfs: "PDFs", awaiting_extraction: "Awaiting extraction", processing: "Processing", awaiting_review: "Awaiting review",
  completed_jobs: "Completed jobs", failed_jobs: "Failed jobs", predicted_cells: "Predicted cells (AI)", corrected_cells: "Corrected cells", approved_cells: "Approved ground truth" };
export default function Dashboard() {
  const { pid, project } = useWs(); const [d, setD] = useState<any>(null);
  useEffect(() => { if (pid) api(`/projects/${pid}/dashboard/`).then(setD).catch(() => setD(null)); }, [pid]);
  if (!pid) return <Notice>Create a project first. <Link className="underline" href="/projects">Go to Projects</Link></Notice>;
  return (<><PageHeader title={`Dashboard · ${project?.name ?? ""}`} />
    {!d ? <p className="text-muted">Loading…</p> : <>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">{Object.keys(L).map((k) => <Stat key={k} label={L[k]} value={d[k]} />)}</div>
      <div className="mt-6 flex flex-wrap gap-2">{[["/data", "Upload documents"], ["/data", "Run extraction"], ["/review", "Review uncertain values"], ["/evaluation", "Evaluate"], ["/export", "Export dataset"]].map(([h, t]) =>
        <Link key={t} href={h} className="rounded-lg border border-line px-4 py-2 text-sm font-medium hover:bg-soft">{t}</Link>)}</div>
      <Card className="mt-6"><h2 className="font-semibold">Recent activity</h2>
        {d.activity.length === 0 ? <p className="mt-2 text-sm text-muted">Nothing yet.</p> : <ul className="mt-2 divide-y divide-line text-sm">{d.activity.map((a: any, i: number) =>
          <li key={i} className="flex justify-between py-2"><span>{a.action} {a.target && `· ${a.target}`}</span><span className="text-muted">{a.user__username} · {new Date(a.created_at).toLocaleString()}</span></li>)}</ul>}</Card>
      <p className="mt-4 text-xs text-muted">AI predictions and approved ground truth are counted separately; only approved cells are ground truth.</p></>}</>);
}

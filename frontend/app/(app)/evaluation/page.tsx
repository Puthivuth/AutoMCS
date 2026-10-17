"use client";
import { useCallback, useEffect, useState } from "react";
import { api, msg } from "@/lib/api";
import { useWs } from "@/lib/workspace";
import { Button, Card, Field, Input, Notice, PageHeader, Select, Stat } from "@/components/ui";
const pct = (v: any) => (v == null ? "–" : (100 * v).toFixed(1) + "%");
export default function Evaluation() {
  const { pid } = useWs(); const [runs, setRuns] = useState<any[]>([]); const [prov, setProv] = useState(""); const [tol, setTol] = useState("0"); const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const load = useCallback(() => { if (pid) api(`/projects/${pid}/evaluations/`).then(setRuns).catch((e) => setErr(msg(e))); }, [pid]);
  useEffect(load, [load]);
  const run = async () => { setBusy(true); setErr(""); try { await api(`/projects/${pid}/evaluations/`, { json: { provider: prov, tolerance: tol } }); load(); } catch (e) { setErr(msg(e)); } setBusy(false); };
  const last = runs[0]?.metrics;
  return (<><PageHeader title="Evaluation" />
    <Card><div className="grid gap-3 sm:grid-cols-3"><Field label="Provider"><Select value={prov} onChange={(e: any) => setProv(e.target.value)}><option value="">Latest prediction (any)</option><option value="gemini">Gemini API</option><option value="deepseek">Local DeepSeek</option></Select></Field>
      <Field label="Numeric tolerance"><Input value={tol} onChange={(e: any) => setTol(e.target.value)} /></Field><div className="flex items-end"><Button variant="primary" disabled={busy} onClick={run}>Run evaluation</Button></div></div>
      <p className="mt-3 text-xs text-muted">Ground truth is approved cells only. Unreviewed predictions are never used as truth. Blank vs blank counts as correct; a blank prediction for a value is “missing”; a value for a blank truth is “extra”.</p></Card>
    {err && <div className="mt-3"><Notice tone="bad">{err}</Notice></div>}
    {last && <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4"><Stat label="Exact cell accuracy" value={pct(last.exact_cell_accuracy)} /><Stat label="Table accuracy" value={pct(last.table_accuracy)} /><Stat label="Document accuracy" value={pct(last.document_accuracy)} />
      <Stat label="Mean abs. error" value={last.mean_abs_error?.toFixed(4)} /><Stat label="Missing" value={last.missing} /><Stat label="Extra" value={last.extra} /><Stat label="Invalid" value={last.invalid} /><Stat label="Cells evaluated" value={last.cells_evaluated} /></div>}
    <h2 className="mb-2 mt-6 font-semibold">History</h2>
    <div className="space-y-2">{runs.map((r) => <Card key={r.id} className="text-sm"><div className="flex justify-between"><b>#{r.id} · {r.provider || "any provider"}</b><span className="text-muted">{new Date(r.created_at).toLocaleString()}</span></div>
      <p className="text-muted">Exact {pct(r.metrics.exact_cell_accuracy)} · tables {pct(r.metrics.table_accuracy)} · docs {pct(r.metrics.document_accuracy)} · cells {r.metrics.cells_evaluated} · tolerance {r.rules.tolerance}</p></Card>)}
      {!runs.length && <p className="text-sm text-muted">No evaluations yet. Approve some cells first.</p>}</div></>);
}

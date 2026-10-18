"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, msg } from "@/lib/api";
import { useWs } from "@/lib/workspace";
import { Badge, Button, Card, Notice, PageHeader, statusTone } from "@/components/ui";

export default function Verify({ params }: { params: { id: string } }) {
  const id = params.id;
  const router = useRouter(); const { pid } = useWs();
  const [doc, setDoc] = useState<any>(null); const [cells, setCells] = useState<any[]>([]); const [page, setPage] = useState(1);
  const [documents, setDocuments] = useState<any[]>([]);
  const [sel, setSel] = useState<any>(null); const [hist, setHist] = useState<any[]>([]); const [saving, setSaving] = useState(""); const [err, setErr] = useState("");
  const [z, setZ] = useState(1); const [pan, setPan] = useState({ x: 0, y: 0 }); const drag = useRef<any>(null); const [nat, setNat] = useState({ w: 1, h: 1 });

  const load = useCallback(async () => { const r = await api(`/documents/${id}/table/`); setDoc(r.document); setCells(r.cells); }, [id]);
  useEffect(() => { load().catch((e) => setErr(msg(e))); }, [load]);
  useEffect(() => { if (pid) api(`/projects/${pid}/documents/`).then(setDocuments).catch(() => setDocuments([])); }, [pid]);
  const pc = cells.filter((c) => c.page_number === page);
  const cols = useMemo(() => [...new Set(pc.sort((a, b) => a.col_index - b.col_index).map((c) => c.column_name))], [pc]);
  const grid = useMemo(() => { const g: any = {}; pc.forEach((c) => { (g[c.row_index] ||= {})[c.col_index] = c; }); return g; }, [pc]);
  const patch = (c: any) => setCells((all) => all.map((x) => (x.id === c.id ? c : x)));
  const shown = (c: any) => (["corrected", "approved"].includes(c.status) ? c.verified_value : c.predicted_value) ?? "";

  async function save(c: any, v: string) {
    if ((v.trim() || null) === (shown(c) || null)) return;
    setSaving("Saving…"); setErr("");
    try { patch(await api(`/cells/${c.id}/label/`, { method: "PATCH", json: { value: v } })); setSaving("Saved"); } catch (e) { setSaving(""); setErr(msg(e)); load(); }
  }
  async function review(c: any, action: string) { try { patch(await api(`/cells/${c.id}/review/`, { json: { action } })); } catch (e) { setErr(msg(e)); } }
  useEffect(() => { if (sel) api(`/cells/${sel.id}/history/`).then(setHist).catch(() => setHist([])); }, [sel?.id, sel?.status, sel?.verified_value]);
  const key = (e: any, r: number, c: number) => {
    const go = (rr: number, cc: number) => document.getElementById(`cell-${rr}-${cc}`)?.focus();
    if (e.key === "Enter" && !e.ctrlKey) { e.preventDefault(); go(r + 1, c); }
    if (e.key === "Enter" && e.ctrlKey) { e.preventDefault(); const cell = grid[r]?.[c]; cell && review(cell, "approve").then(() => go(r + 1, c)); }
    if (e.key === "ArrowDown") go(r + 1, c); if (e.key === "ArrowUp") go(r - 1, c);
  };
  const bb = sel?.bbox && sel.page_number === page ? sel.bbox : null;
  const docIndex = documents.findIndex((item: any) => item.id === Number(id));
  const moveDocument = (offset: number) => { const next = documents[docIndex + offset]; if (next) router.push(`/verify/${next.id}`); };

  if (!doc) return err ? <Notice tone="bad">{err}</Notice> : <p className="text-muted">Loading…</p>;
    return (<><PageHeader title={doc.original_name}>
      {documents.length > 1 && <><Button size="sm" disabled={docIndex <= 0} onClick={() => moveDocument(-1)}>← Previous</Button><span className="self-center text-xs text-muted">{docIndex + 1}/{documents.length}</span><Button size="sm" disabled={docIndex < 0 || docIndex >= documents.length - 1} onClick={() => moveDocument(1)}>Next →</Button></>}
      <span className="self-center text-sm text-muted">{saving}</span>
      {doc.page_count > 1 && <><Button size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>‹</Button><span className="self-center text-sm">Page {page}/{doc.page_count}</span><Button size="sm" disabled={page >= doc.page_count} onClick={() => setPage(page + 1)}>›</Button></>}
      <Button variant="primary" onClick={async () => { try { const r = await api(`/documents/${id}/approve/`, { json: {} }); setErr(r.skipped ? `${r.skipped} invalid or rejected cell(s) need correction first.` : ""); load(); } catch (e) { setErr(msg(e)); } }}>Approve all valid</Button></PageHeader>
    {err && <div className="mb-3"><Notice tone="bad">{err}</Notice></div>}
    <div className="grid gap-4 xl:grid-cols-2">
      <Card className="p-3"><div className="mb-2 flex items-center gap-2 text-xs text-muted"><Button size="sm" onClick={() => setZ(z * 1.25)}>+</Button><Button size="sm" onClick={() => setZ(Math.max(0.3, z / 1.25))}>−</Button><Button size="sm" onClick={() => { setZ(1); setPan({ x: 0, y: 0 }); }}>Fit A4</Button><span>A4 page fit; drag to pan after zooming</span></div>
        <div className="relative mx-auto aspect-[210/297] max-h-[72vh] w-full max-w-[794px] cursor-grab overflow-hidden rounded-lg bg-soft"
          onWheel={(e) => setZ((v) => Math.min(6, Math.max(0.3, v * (e.deltaY < 0 ? 1.1 : 0.9))))}
          onPointerDown={(e) => { drag.current = { x: e.clientX - pan.x, y: e.clientY - pan.y }; (e.target as any).setPointerCapture?.(e.pointerId); }}
          onPointerMove={(e) => drag.current && setPan({ x: e.clientX - drag.current.x, y: e.clientY - drag.current.y })} onPointerUp={() => (drag.current = null)}>
          <div className="relative h-full w-full origin-top-left" style={{ transform: `translate(${pan.x}px,${pan.y}px) scale(${z})` }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={`/api/documents/${id}/pages/${page}/image/`} alt="Original document" draggable={false} className="block h-full w-full object-contain" onLoad={(e: any) => setNat({ w: e.target.naturalWidth, h: e.target.naturalHeight })} />
            {bb && <div className="pointer-events-none absolute border-2 border-brand bg-brand/20" style={{ left: `${(100 * bb[0]) / nat.w}%`, top: `${(100 * bb[1]) / nat.h}%`, width: `${(100 * (bb[2] - bb[0])) / nat.w}%`, height: `${(100 * (bb[3] - bb[1])) / nat.h}%` }} />}
          </div></div></Card>
      <div className="space-y-4"><Card className="overflow-x-auto p-3">
        {!pc.length ? <p className="p-3 text-sm text-muted">No extracted table for this page. Run extraction or add labels from Data.</p> :
          <table className="w-full text-sm"><thead><tr className="text-left text-muted"><th className="p-1">No</th>{cols.map((c: any) => <th key={c} className="p-1">{c}</th>)}</tr></thead>
            <tbody>{Object.keys(grid).map(Number).sort((a, b) => a - b).map((r) => <tr key={r}><td className="p-1 text-muted">{r + 1}</td>
              {cols.map((_: any, ci: number) => { const c = grid[r]?.[ci]; if (!c) return <td key={ci} />;
                const isCode = (c.column_name || "").toLowerCase() === "code";
                const ring = c.status === "approved" ? "border-ok bg-ok/10" : c.status === "rejected" || c.flags.includes("invalid_decimal") ? "border-bad" : c.status === "corrected" ? "border-brand" : c.flags.length ? "border-warn" : "border-line";
                return <td key={ci} className="p-1"><input id={`cell-${r}-${ci}`} defaultValue={shown(c)} key={`${c.id}-${c.status}-${c.verified_value}-${c.predicted_value}`} placeholder="null" inputMode={isCode ? "text" : "decimal"}
                  className={`${isCode ? "w-28" : "w-20"} rounded border bg-bg px-1.5 py-1 tabular-nums ${ring}`} onFocus={() => setSel(c)} onBlur={(e) => save(c, e.target.value)} onKeyDown={(e) => key(e, r, ci)} /></td>; })}</tr>)}</tbody></table>}
        <p className="mt-3 text-xs text-muted">Enter moves down, Ctrl+Enter approves the cell and moves down. Edits are normalized to two decimals; the raw AI prediction is kept in history.</p></Card>
      {sel && <Card><div className="flex items-center justify-between"><h2 className="font-semibold">Row {sel.row_index + 1} · column {sel.column_name}</h2><Badge tone={statusTone(sel.status)}>{sel.status}</Badge></div>
        <p className="mt-1 text-sm text-muted">Raw: {sel.raw_text ?? "null"} · AI: {sel.predicted_value ?? "null"} {sel.flags.map((f: string) => <Badge key={f} tone="warn">{f.replace("_", " ")}</Badge>)}</p>
        <div className="mt-3 flex gap-2"><Button size="sm" variant="primary" onClick={() => review(sel, "approve").then(() => setSel(null))}>Approve</Button><Button size="sm" variant="danger" onClick={() => review(sel, "reject")}>Reject</Button><Button size="sm" onClick={() => review(sel, "reopen")}>Reopen</Button></div>
        <ul className="mt-3 max-h-40 divide-y divide-line overflow-auto text-xs text-muted">{hist.map((h) => <li key={h.id} className="py-1">{new Date(h.created_at).toLocaleString()} · {h.action} ({h.source}) {h.old_value ?? "null"} → {h.new_value ?? "null"} {h.user && `· ${h.user}`}</li>)}</ul></Card>}</div></div></>);
}

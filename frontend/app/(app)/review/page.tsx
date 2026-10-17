"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, msg } from "@/lib/api";
import { useWs } from "@/lib/workspace";
import { Badge, Notice, PageHeader, Select, statusTone, Table } from "@/components/ui";
const R = [["flagged", "All flagged"], ["invalid_decimal", "Invalid decimals"], ["rounded", "Changed by rounding"], ["low_confidence", "Low confidence"], ["pending_approval", "Corrected, awaiting approval"]];
export default function Review() {
  const { pid } = useWs(); const [reason, setReason] = useState("flagged"); const [prov, setProv] = useState(""); const [d, setD] = useState<any>(null); const [err, setErr] = useState("");
  useEffect(() => { if (pid) api(`/projects/${pid}/review-queue/?reason=${reason}${prov ? `&provider=${prov}` : ""}`).then(setD).catch((e) => setErr(msg(e))); }, [pid, reason, prov]);
  return (<><PageHeader title="Review queue"><Select className="!w-56" value={reason} onChange={(e: any) => setReason(e.target.value)}>{R.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</Select>
    <Select className="!w-40" value={prov} onChange={(e: any) => setProv(e.target.value)}><option value="">Any provider</option><option value="gemini">Gemini</option><option value="deepseek">DeepSeek</option></Select></PageHeader>
    {err && <Notice tone="bad">{err}</Notice>}
    {d?.invalid_json?.length > 0 && <div className="mb-3"><Notice>Invalid model output on {d.invalid_json.length} document(s): {d.invalid_json.map((x: any) => <Link key={x.document} className="underline mr-2" href={`/verify/${x.document}`}>{x.document__original_name}</Link>)}</Notice></div>}
    <Table><thead className="bg-soft text-muted"><tr><th className="p-2">Document</th><th>Cell</th><th>Raw</th><th>AI value</th><th>Flags</th><th>Status</th></tr></thead>
      <tbody>{d?.cells.map((c: any) => <tr key={c.id} className="border-t border-line"><td className="p-2"><Link className="underline" href={`/verify/${c.document}`}>{c.document_name}</Link></td><td>r{c.row_index + 1} · {c.column_name}</td><td>{c.raw_text ?? "null"}</td><td>{c.predicted_value ?? "null"}</td>
        <td>{c.flags.map((f: string) => <Badge key={f} tone="warn">{f.replace("_", " ")}</Badge>)}</td><td><Badge tone={statusTone(c.status)}>{c.status}</Badge></td></tr>)}
        {d && !d.cells.length && <tr><td colSpan={6} className="p-4 text-center text-muted">Nothing needs review.</td></tr>}</tbody></Table></>);
}

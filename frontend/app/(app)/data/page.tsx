"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { api, msg } from "@/lib/api";
import { useWs } from "@/lib/workspace";
import { Badge, Button, Card, Field, Notice, PageHeader, Select, Table, statusTone } from "@/components/ui";

const supported = ["image/png", "image/jpeg", "image/webp", "application/pdf"];
const size = (n: number) => n < 1024 * 1024 ? `${(n / 1024).toFixed(0)} KB` : `${(n / 1024 / 1024).toFixed(1)} MB`;

export default function Data() {
  const { pid } = useWs();
  const picker = useRef<HTMLInputElement>(null);
  const folderPicker = useRef<HTMLInputElement>(null);
  const [docs, setDocs] = useState<any[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [providers, setProviders] = useState<any[]>([]);
  const [provider, setProvider] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [jobId, setJobId] = useState<number | null>(null);
  const [err, setErr] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    if (!pid) return;
    try {
      const [documents, available] = await Promise.all([api(`/projects/${pid}/documents/`), api("/providers/")]);
      setDocs(documents); setProviders(available);
      if (!provider) setProvider(available.find((x: any) => x.default && x.ready)?.name || available.find((x: any) => x.ready)?.name || "");
    } catch (e) { setErr(msg(e)); }
  };
  useEffect(() => { load(); }, [pid]);
  useEffect(() => { setSelected((ids) => ids.filter((id) => docs.some((doc: any) => doc.id === id))); }, [docs]);
  useEffect(() => {
    if (!pid || !jobId) return;
    let active = true;
    const poll = async () => {
      try {
        const jobs = await api(`/projects/${pid}/jobs/`);
        const job = jobs.find((item: any) => item.id === jobId);
        if (!active || !job) return;
        if (["queued", "running"].includes(job.status)) {
          setNotice(`Extraction ${job.status}...`);
          window.setTimeout(poll, 2000);
        } else {
          setNotice(job.status === "completed" ? "Extraction completed." : `Extraction ${job.status}: ${job.error || "check the job details"}`);
          setJobId(null); await load();
        }
      } catch (e) { if (active) setErr(msg(e)); }
    };
    poll();
    return () => { active = false; };
  }, [jobId, pid]);

  const choose = (event: any) => {
    const picked = Array.from(event.target.files || []) as File[];
    setFiles(picked.filter((file) => supported.includes(file.type)));
    setNotice(picked.some((file) => !supported.includes(file.type)) ? "Unsupported files were skipped. Supported formats: PNG, JPEG, WebP, PDF." : "");
    event.target.value = "";
  };

  const upload = async () => {
    if (!pid || !files.length) return;
    setUploading(true); setErr(""); setNotice("Uploading files...");
    try {
      const form = new FormData();
      files.forEach((file) => { form.append("files", file); form.append("paths", (file as any).webkitRelativePath || file.name); });
      const result = await api(`/projects/${pid}/documents/`, { form });
      const created = result.results?.filter((x: any) => x.status === "created").length || 0;
      const duplicates = result.results?.filter((x: any) => x.status === "duplicate").length || 0;
      setFiles([]); setNotice(`Imported ${created} file(s). ${duplicates ? `${duplicates} duplicate(s) skipped.` : ""}`); await load();
    } catch (e) { setErr(msg(e)); setNotice(""); }
    setUploading(false);
  };

  const extractDocs = async (targetDocs: number[]) => {
    if (!pid || !provider || !targetDocs.length) return;
    setExtracting(true); setErr("");
    try {
      const job = await api(`/projects/${pid}/extract/`, { json: { provider, document_ids: targetDocs } });
      setJobId(job.id);
      setNotice(`Extraction started for ${targetDocs.length} document(s). Processing now...`);
      await load();
    } catch (e) {
      setErr(msg(e));
    }
    setExtracting(false);
  };
  const extractAll = () => extractDocs(docs.map((doc: any) => doc.id));
  const extractSelected = () => extractDocs(selected);

  const removeSelected = async () => {
    if (!pid || !selected.length || !confirm(`Delete ${selected.length} selected document(s)? This also removes their extracted data.`)) return;
    setErr(""); setNotice("Deleting selected documents...");
    try { await api(`/projects/${pid}/documents/`, { method: "DELETE", json: { document_ids: selected } }); setSelected([]); setNotice("Selected documents deleted."); await load(); }
    catch (e) { setErr(msg(e)); setNotice(""); }
  };
  const toggleAll = (checked: boolean) => setSelected(checked ? docs.map((doc: any) => doc.id) : []);
  const toggle = (id: number) => setSelected((ids) => ids.includes(id) ? ids.filter((item) => item !== id) : [...ids, id]);

  return (<><PageHeader title="Data & AI Extraction" />
    <Card>
      <h2 className="font-semibold">Import project data</h2>
      <p className="mt-1 text-sm text-muted">Choose images, a whole image folder, or PDF documents. Every file is stored under the selected project.</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button onClick={() => picker.current?.click()}>Choose images or PDFs</Button>
        <Button onClick={() => folderPicker.current?.click()}>Choose image folder</Button>
        <input ref={picker} type="file" accept="image/png,image/jpeg,image/webp,application/pdf" multiple className="hidden" onChange={choose} />
        <input ref={folderPicker} type="file" accept="image/png,image/jpeg,image/webp,application/pdf" multiple className="hidden" {...({ webkitdirectory: "", directory: "" } as any)} onChange={choose} />
      </div>
      {files.length > 0 && <div className="mt-4 rounded-lg border border-line p-3"><div className="mb-2 flex items-center justify-between"><b>{files.length} file(s) ready</b><Button size="sm" variant="primary" disabled={uploading} onClick={upload}>{uploading ? "Uploading..." : "Upload files"}</Button></div><ul className="max-h-40 space-y-1 overflow-auto text-sm text-muted">{files.map((file) => <li key={`${file.name}-${file.size}`}>{(file as any).webkitRelativePath || file.name} <span className="text-xs">({size(file.size)})</span></li>)}</ul></div>}
      {notice && <div className="mt-3"><Notice tone="ok">{notice}</Notice></div>}
      {err && <div className="mt-3"><Notice tone="bad">{err}</Notice></div>}
    </Card>

    <Card className="mt-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <Field label="AI provider">
          <Select value={provider} onChange={(e: any) => setProvider(e.target.value)}>
            <option value="">Select a ready provider</option>
            {providers.map((item: any) => <option key={item.name} value={item.name} disabled={!item.ready}>{item.label || item.name}{!item.ready ? " (not ready)" : ""}</option>)}
          </Select>
        </Field>
        <div className="flex flex-wrap gap-2">
          <Button variant="primary" disabled={!provider || !selected.length || extracting || !!jobId} onClick={extractSelected}>
            {extracting || jobId ? "Extracting..." : `Extract selected (${selected.length})`}
          </Button>
          <Button disabled={!provider || !docs.length || extracting || !!jobId} onClick={extractAll}>
            {extracting || jobId ? "Extracting..." : "Extract all documents"}
          </Button>
        </div>
      </div>
      {providers.filter((item: any) => !item.ready).map((item: any) => <p key={item.name} className="mt-2 text-xs text-warn">{item.label || item.name}: {item.problems?.join("; ")}</p>)}
    </Card>

    <div className="mt-4">
      <div className="mb-2 flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm text-muted">
          <input type="checkbox" checked={!!docs.length && selected.length === docs.length} onChange={(e) => toggleAll(e.target.checked)} /> Select all
        </label>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="primary" disabled={!provider || !selected.length || extracting || !!jobId} onClick={extractSelected}>
            Extract selected ({selected.length})
          </Button>
          <Button size="sm" variant="danger" disabled={!selected.length} onClick={removeSelected}>
            Delete selected ({selected.length})
          </Button>
        </div>
      </div>
      <Table><thead className="bg-soft text-muted"><tr><th className="p-2"><span className="sr-only">Select</span></th><th>Document</th><th>Type</th><th>Size</th><th>Pages</th><th>Status</th><th /></tr></thead><tbody>{docs.map((doc: any) => <tr key={doc.id} className="border-t border-line"><td className="p-2"><input type="checkbox" checked={selected.includes(doc.id)} onChange={() => toggle(doc.id)} aria-label={`Select ${doc.original_name}`} /></td><td>{doc.relative_path || doc.original_name}</td><td>{doc.kind}</td><td>{size(doc.size)}</td><td>{doc.page_count}</td><td><Badge tone={statusTone(doc.status)}>{doc.status}</Badge></td><td><Link className="text-brand underline" href={`/verify/${doc.id}`}>Compare</Link></td></tr>)}{!docs.length && <tr><td colSpan={7} className="p-5 text-center text-muted">No documents yet. Import images, a folder, or PDFs above.</td></tr>}</tbody></Table>
    </div>
  </>);
}

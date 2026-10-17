"use client";
import { useCallback, useEffect, useState } from "react";
import { api, msg } from "@/lib/api";
import { useWs } from "@/lib/workspace";
import { Badge, Button, Card, Field, Input, Notice, PageHeader, Select, statusTone } from "@/components/ui";
export default function Settings() {
  const { user } = useWs(); const [m, setM] = useState<any>(null); const [s, setS] = useState<any>(null); const [err, setErr] = useState(""); const [ok, setOk] = useState("");
  const load = useCallback(() => { api("/models/local/status/").then(setM).catch((e) => setErr(msg(e))); }, []);
  useEffect(() => { load(); if (user.is_admin) api("/settings/").then(setS).catch(() => {}); }, [load, user.is_admin]);
  useEffect(() => { if (!m || !["downloading", "loading"].includes(m.status)) return; const t = setInterval(load, 2500); return () => clearInterval(t); }, [m, load]);
  return (<><PageHeader title="Settings" />{err && <Notice tone="bad">{err}</Notice>}
    <div className="grid gap-4 lg:grid-cols-2">
      <Card><div className="flex items-center justify-between"><h2 className="font-semibold">Local DeepSeek 1.5B</h2>{m && <Badge tone={statusTone(m.status)}>{m.status}</Badge>}</div>
        {m && <><p className="mt-2 text-sm text-muted">{m.repo} @ {m.revision || "no pinned revision"}<br />{m.path}</p>
          <div className="mt-3 h-2 overflow-hidden rounded bg-soft"><div className="h-full bg-accent" style={{ width: `${m.progress}%` }} /></div>
          <p className="mt-2 text-xs text-muted">{m.detail || (m.installed ? "Files installed and verified." : "Files not installed.")} · auto-download {m.auto_download ? "on" : "off"} · {m.loaded ? "loaded in this process" : "not loaded here"}</p>
          {m.problems.length > 0 && <div className="mt-2"><Notice tone="bad">{m.problems.join(" ")}</Notice></div>}</>}
        {user.is_admin ? <Button className="mt-3" onClick={() => api("/models/local/prepare/", { json: {} }).then(() => { setOk("Preparation queued."); setTimeout(load, 1500); }).catch((e) => setErr(msg(e)))}>Download / load now</Button> : <p className="mt-3 text-xs text-muted">Only administrators can start model preparation.</p>}
        {ok && <p className="mt-2 text-xs text-ok">{ok}</p>}</Card>
      {user.is_admin && s && <Card><h2 className="font-semibold">Site and provider settings</h2>
        <Field label="Default provider"><Select value={s.default_provider} onChange={(e: any) => setS({ ...s, default_provider: e.target.value })}><option value="gemini">Gemini API</option><option value="deepseek">Local DeepSeek</option></Select></Field>
        {["gemini_model", "supervisor", "institution", "contact_email"].map((k) => <Field key={k} label={k.replace("_", " ")}><Input value={s[k] || ""} onChange={(e: any) => setS({ ...s, [k]: e.target.value })} /></Field>)}
        <p className="mt-2 text-xs text-muted">The Gemini API key is read from the server environment and is never shown here.</p>
        <Button variant="primary" className="mt-3" onClick={() => api("/settings/", { method: "PATCH", json: s }).then(() => setOk("Saved.")).catch((e) => setErr(msg(e)))}>Save</Button></Card>}</div></>);
}

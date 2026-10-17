"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, msg } from "@/lib/api";
import { Button, Card, Field, Input, Notice } from "@/components/ui";
export default function Login() {
  const router = useRouter();
  const [u, setU] = useState(""); const [p, setP] = useState(""); const [show, setShow] = useState(false);
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const submit = async (e: any) => {
    e.preventDefault(); setErr("");
    if (!u.trim() || !p) return setErr("Enter your username (or email) and password.");
    setBusy(true);
    try { await api("/auth/login/", { json: { username: u, password: p } }); router.push("/dashboard"); } catch (x) { setErr(msg(x)); setBusy(false); }
  };
  return (<Card className="mx-auto mt-6 max-w-sm"><h1 className="text-2xl font-semibold">Login</h1>
    <form onSubmit={submit} className="mt-4">
      <Field label="Username or email"><Input autoComplete="username" value={u} onChange={(e: any) => setU(e.target.value)} /></Field>
      <Field label="Password"><div className="flex gap-2"><Input type={show ? "text" : "password"} autoComplete="current-password" value={p} onChange={(e: any) => setP(e.target.value)} />
        <Button type="button" onClick={() => setShow(!show)}>{show ? "Hide" : "Show"}</Button></div></Field>
      {err && <div className="mt-3"><Notice tone="bad">{err}</Notice></div>}
      <Button variant="primary" className="mt-4 w-full" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</Button></form>
    <p className="mt-4 text-xs text-muted">Accounts are created by an administrator.</p></Card>);
}

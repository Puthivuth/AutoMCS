"use client";
import { useEffect, useState } from "react";
import { api, msg } from "@/lib/api";
import { Button, Card, Field, Input, Notice, Textarea } from "@/components/ui";
export default function Contact() {
  const [f, setF] = useState({ name: "", email: "", message: "", website: "" });
  const [state, setState] = useState<any>(null); const [email, setEmail] = useState("");
  useEffect(() => { fetch("/api/public/config/").then((r) => r.json()).then((c) => setEmail(c.contact_email || "")).catch(() => {}); }, []);
  const submit = async (e: any) => {
    e.preventDefault(); setState(null);
    try { await api("/contact/", { json: f }); setState({ ok: true }); } catch (x) { setState({ err: msg(x) }); }
  };
  return (<div className="mx-auto max-w-xl"><h1 className="text-3xl font-semibold tracking-tight">Contact</h1>
    <p className="mt-2 text-sm text-muted">{email ? <>Email: {email}</> : "Approved contact details will appear here once configured."}</p>
    <Card className="mt-6">{state?.ok ? <Notice tone="ok">Thank you, your message was sent.</Notice> : (
      <form onSubmit={submit}>
        <Field label="Name"><Input required value={f.name} onChange={(e: any) => setF({ ...f, name: e.target.value })} /></Field>
        <Field label="Email"><Input type="email" required value={f.email} onChange={(e: any) => setF({ ...f, email: e.target.value })} /></Field>
        <Field label="Message"><Textarea rows={5} required minLength={10} value={f.message} onChange={(e: any) => setF({ ...f, message: e.target.value })} /></Field>
        <input className="hidden" tabIndex={-1} autoComplete="off" value={f.website} onChange={(e) => setF({ ...f, website: e.target.value })} aria-hidden />
        {state?.err && <div className="mt-3"><Notice tone="bad">{state.err}</Notice></div>}
        <Button variant="primary" className="mt-4">Send message</Button></form>)}</Card></div>);
}

import Link from "next/link";
import { Card } from "@/components/ui";
const steps = [["Import", "Images, whole folders, or PDFs, kept in isolated projects."], ["Extract", "Choose Gemini or a local DeepSeek pipeline for each job."],
  ["Verify", "Compare the source beside the table, correct, then approve."], ["Evaluate", "Measure accuracy against verified labels only."], ["Export", "Originals plus JSON and CSV ground truth in one ZIP."]];
export default function Home() {
  return (<>
    <section className="mx-auto max-w-3xl py-10 text-center">
      <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Label decimal tables in minutes, not days</h1>
      <p className="mx-auto mt-4 max-w-xl text-lg text-muted">AutoMCS extracts values from table images and PDFs, lets you verify every cell, and exports reliable ground-truth datasets for research.</p>
      <div className="mt-7 flex justify-center gap-3"><Link href="/login" className="rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-onaccent">Login to workspace</Link>
        <Link href="/about" className="rounded-lg border border-line px-5 py-2.5 text-sm font-medium hover:bg-soft">About the project</Link></div>
    </section>
    <h2 className="mt-10 text-xl font-semibold">How it works</h2>
    <ol className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{steps.map(([t, d], i) => (<li key={t}><Card className="h-full"><div className="text-sm text-muted">Step {i + 1}</div><div className="mt-1 font-semibold">{t}</div><p className="mt-1 text-sm text-muted">{d}</p></Card></li>))}</ol>
    <h2 className="mt-12 text-xl font-semibold">Example output (synthetic)</h2>
    <Card className="mt-4 overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left text-muted"><th className="p-2">No</th>{["I", "II", "III", "IV", "V"].map((c) => <th key={c} className="p-2">{c}</th>)}</tr></thead>
      <tbody><tr className="border-t border-line"><td className="p-2">1</td><td>13.45</td><td>14.56</td><td className="text-muted">null</td><td className="text-muted">null</td><td className="text-muted">null</td></tr>
        <tr className="border-t border-line"><td className="p-2">2</td><td>5.10</td><td>5.13</td><td>12.00</td><td className="text-muted">null</td><td className="text-muted">null</td></tr></tbody></table>
      <p className="mt-3 text-sm text-muted">Values are stored as two-decimal strings. Blank cells stay null, and AI predictions never count as ground truth until approved.</p></Card>
    <div className="mt-12 grid gap-3 sm:grid-cols-2">{[["Less repetitive work", "Batch extraction replaces typing every cell by hand."], ["Predictions stay separate", "Raw output, corrections and approved labels are never mixed."],
      ["Reproducible", "Every run records its provider, model and settings."], ["Private", "Documents and labels are visible only after login."]].map(([t, d]) => <Card key={t}><div className="font-semibold">{t}</div><p className="mt-1 text-sm text-muted">{d}</p></Card>)}</div>
  </>);
}

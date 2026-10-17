import React from "react";
const cx = (...a: any[]) => a.filter(Boolean).join(" ");
export function Button({ variant = "default", size = "md", className, ...p }: any) {
  const v: any = { default: "border border-line bg-bg hover:bg-soft", primary: "bg-accent text-onaccent hover:opacity-90 border border-accent", danger: "border border-bad text-bad hover:bg-bad/10", ghost: "hover:bg-soft" };
  return <button {...p} className={cx("inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition disabled:cursor-not-allowed disabled:opacity-50", size === "sm" ? "px-2.5 py-1 text-xs" : "px-4 py-2 text-sm", v[variant], className)} />;
}
export const Card = ({ className, ...p }: any) => <div {...p} className={cx("rounded-xl border border-line bg-bg p-5", className)} />;
export const Input = React.forwardRef<HTMLInputElement, any>(({ className, ...p }, r) => <input ref={r} {...p} className={cx("w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm placeholder:text-muted", className)} />);
Input.displayName = "Input";
export const Select = ({ className, ...p }: any) => <select {...p} className={cx("w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm", className)} />;
export const Textarea = ({ className, ...p }: any) => <textarea {...p} className={cx("w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm", className)} />;
export const Field = ({ label, children }: any) => <label className="mt-4 block text-sm font-medium first:mt-0">{label}<div className="mt-1.5 font-normal">{children}</div></label>;
export function Badge({ tone = "neutral", children }: any) {
  const t: any = { neutral: "bg-soft text-muted", ok: "bg-ok/15 text-ok", warn: "bg-warn/15 text-warn", bad: "bg-bad/15 text-bad", info: "bg-brand/15 text-brand" };
  return <span className={cx("inline-block rounded-full px-2.5 py-0.5 text-xs font-medium", t[tone])}>{children}</span>;
}
export const Stat = ({ label, value }: any) => <Card><div className="text-3xl font-semibold tracking-tight">{value ?? "–"}</div><div className="mt-1 text-sm text-muted">{label}</div></Card>;
export const PageHeader = ({ title, children }: any) => <div className="mb-6 flex flex-wrap items-center justify-between gap-3"><h1 className="text-2xl font-semibold tracking-tight">{title}</h1><div className="flex gap-2">{children}</div></div>;
export const Notice = ({ tone = "neutral", children }: any) => <div className={cx("rounded-lg border px-3 py-2 text-sm", tone === "bad" ? "border-bad/40 bg-bad/10 text-bad" : tone === "ok" ? "border-ok/40 bg-ok/10 text-ok" : "border-line bg-soft text-muted")}>{children}</div>;
export const Table = ({ children }: any) => <div className="overflow-x-auto rounded-xl border border-line"><table className="w-full text-left text-sm">{children}</table></div>;
export const statusTone = (s: string) => ({ approved: "ok", done: "ok", completed: "ok", ready: "ok", needs_review: "warn", running: "info", queued: "info", downloading: "info", loading: "info", failed: "bad", completed_with_errors: "warn", corrected: "info", rejected: "bad", unreviewed: "warn" } as any)[s] || "neutral";

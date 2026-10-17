export class ApiError extends Error { status: number; data: any; constructor(m: string, s: number, d: any) { super(m); this.status = s; this.data = d; } }
const cookie = (n: string) => document.cookie.split("; ").find((r) => r.startsWith(n + "="))?.split("=")[1] || "";

export async function api<T = any>(path: string, opts: { method?: string; json?: any; form?: FormData } = {}): Promise<T> {
  const method = (opts.method || (opts.json || opts.form ? "POST" : "GET")).toUpperCase();
  const headers: Record<string, string> = {};
  if (method !== "GET") {
    if (!cookie("csrftoken")) await fetch("/api/auth/csrf/", { credentials: "include" });
    headers["X-CSRFToken"] = cookie("csrftoken");
  }
  let body: any;
  if (opts.json !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(opts.json); }
  if (opts.form) body = opts.form;
  const r = await fetch("/api" + path, { method, headers, body, credentials: "include" });
  const data = r.status === 204 ? null : await r.json().catch(() => null);
  if (!r.ok) throw new ApiError(data?.detail || (data && JSON.stringify(data)) || `Request failed (${r.status})`, r.status, data);
  return data as T;
}
export const msg = (e: any) => (e instanceof Error ? e.message : String(e));

"use client";
import { useCallback, useEffect, useState } from "react";
import { api, msg } from "@/lib/api";
import { useWs } from "@/lib/workspace";
import { Badge, Button, Card, Field, Input, Notice, PageHeader, Select } from "@/components/ui";

export default function Settings() {
  const { user } = useWs();
  const [s, setS] = useState<any>(null);
  const [keys, setKeys] = useState<{ [key: string]: string }>({
    gemini_api_key_1: "",
    gemini_api_key_2: "",
    gemini_api_key_3: "",
    gemini_api_key_4: "",
  });
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    if (user.is_admin) {
      api("/settings/")
        .then((data) => {
          setS(data);
          setKeys({
            gemini_api_key_1: data.gemini_api_key_1 || "",
            gemini_api_key_2: data.gemini_api_key_2 || "",
            gemini_api_key_3: data.gemini_api_key_3 || "",
            gemini_api_key_4: data.gemini_api_key_4 || "",
          });
        })
        .catch((e) => setErr(msg(e)));
    }
  }, [user.is_admin]);

  useEffect(() => {
    load();
  }, [load]);

  // Periodic poll if any key is cooling down
  useEffect(() => {
    if (!s?.gemini_keys?.some((k: any) => k.cooling)) return;
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [s, load]);

  const save = async () => {
    setSaving(true);
    setErr("");
    setOk("");
    try {
      const payload = { ...s, ...keys };
      const updated = await api("/settings/", { method: "PATCH", json: payload });
      setS(updated);
      setOk("Settings saved successfully.");
    } catch (e) {
      setErr(msg(e));
    }
    setSaving(false);
  };

  const resetCooldowns = async () => {
    setErr("");
    setOk("");
    try {
      const updated = await api("/settings/", { method: "PATCH", json: { reset_cooldowns: true } });
      setS(updated);
      setOk("Key cooldowns reset.");
    } catch (e) {
      setErr(msg(e));
    }
  };

  return (
    <>
      <PageHeader title="Settings" />
      {err && <div className="mb-3"><Notice tone="bad">{err}</Notice></div>}
      {ok && <div className="mb-3"><Notice tone="ok">{ok}</Notice></div>}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Gemini Multi-Key Pool (API 1 - 4)</h2>
            <Badge tone="brand">Auto-Failover Active</Badge>
          </div>
          <p className="mt-2 text-sm text-muted">
            Configure up to 4 Gemini API keys. When one key runs out of tokens or hits quota limits (HTTP 429), AutoMCS automatically switches to the next available key (1 → 2 → 3 → 4) so extraction is not interrupted.
          </p>

          <div className="mt-4 space-y-3">
            {[1, 2, 3, 4].map((idx) => {
              const info = s?.gemini_keys?.find((k: any) => k.index === idx);
              const keyField = `gemini_api_key_${idx}`;
              return (
                <div key={idx} className="rounded-lg border border-line p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Gemini API {idx}</span>
                    {info?.cooling ? (
                      <Badge tone="warn">Rate-limited ({info.cooldown_remaining}s)</Badge>
                    ) : info?.configured ? (
                      <Badge tone="ok">Ready ({info.source})</Badge>
                    ) : (
                      <Badge tone="muted">Not configured</Badge>
                    )}
                  </div>
                  {user.is_admin ? (
                    <div className="mt-2">
                      <Input
                        type="password"
                        placeholder={info?.masked ? `Configured (${info.masked})` : `Paste Gemini API Key ${idx}...`}
                        value={keys[keyField] || ""}
                        onChange={(e: any) => setKeys({ ...keys, [keyField]: e.target.value })}
                      />
                    </div>
                  ) : (
                    <p className="mt-1 text-xs text-muted">
                      {info?.masked ? `Key: ${info.masked}` : "Key not configured."}
                    </p>
                  )}
                </div>
              );
            })}
          </div>

          {user.is_admin && (
            <div className="mt-4 flex flex-wrap gap-2">
              <Button variant="primary" disabled={saving} onClick={save}>
                {saving ? "Saving..." : "Save API keys"}
              </Button>
              {s?.gemini_keys?.some((k: any) => k.cooling) && (
                <Button onClick={resetCooldowns}>Reset key cooldowns</Button>
              )}
            </div>
          )}
        </Card>

        {user.is_admin && s && (
          <Card>
            <h2 className="font-semibold">Site and Extraction Settings</h2>
            <div className="mt-3 space-y-3">
              <Field label="Default provider">
                <Select
                  value={s.default_provider || "gemini"}
                  onChange={(e: any) => setS({ ...s, default_provider: e.target.value })}
                >
                  <option value="gemini">Gemini API (Auto-switch 1-4)</option>
                  <option value="gemini_1">Gemini API 1</option>
                  <option value="gemini_2">Gemini API 2</option>
                  <option value="gemini_3">Gemini API 3</option>
                  <option value="gemini_4">Gemini API 4</option>
                </Select>
              </Field>

              <Field label="Gemini vision model">
                <Input
                  value={s.gemini_model || ""}
                  placeholder="gemini-3.8-flash"
                  onChange={(e: any) => setS({ ...s, gemini_model: e.target.value })}
                />
              </Field>

              {["supervisor", "institution", "contact_email"].map((k) => (
                <Field key={k} label={k.replace("_", " ")}>
                  <Input
                    value={s[k] || ""}
                    onChange={(e: any) => setS({ ...s, [k]: e.target.value })}
                  />
                </Field>
              ))}
            </div>

            <Button variant="primary" className="mt-4" disabled={saving} onClick={save}>
              {saving ? "Saving..." : "Save settings"}
            </Button>
          </Card>
        )}
      </div>
    </>
  );
}

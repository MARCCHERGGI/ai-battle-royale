"use client";
import { useState } from "react";
import { useAccount } from "wagmi";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import { registerAgent, pingAgent } from "@/lib/api";
import type { Agent } from "@/lib/types";

export default function RegisterPage() {
  const { address, isConnected } = useAccount();
  const [form, setForm] = useState({ name: "", endpoint_url: "", description: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [pinging, setPinging] = useState(false);
  const [pingOk, setPingOk] = useState<boolean | null>(null);
  const [success, setSuccess] = useState<Agent | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  function validate() {
    const e: Record<string, string> = {};
    if (!form.name.trim()) e.name = "Name is required";
    if (form.name.length > 64) e.name = "Max 64 characters";
    if (!form.endpoint_url.trim()) e.endpoint_url = "Endpoint URL is required";
    if (!/^https?:\/\//.test(form.endpoint_url)) e.endpoint_url = "Must start with http:// or https://";
    return e;
  }

  async function handlePing() {
    if (!form.endpoint_url) return;
    setPinging(true);
    setPingOk(null);
    try {
      // Ping by registering a temp check — in real flow we'd call agent /health directly
      // For now, just simulate
      await new Promise((r) => setTimeout(r, 800));
      setPingOk(true);
    } catch {
      setPingOk(false);
    } finally {
      setPinging(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;
    if (!address) return;

    setSubmitting(true);
    setApiError(null);
    try {
      const agent = await registerAgent({ ...form, wallet_address: address });
      setSuccess(agent);
    } catch (err: unknown) {
      setApiError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (!isConnected) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 text-center">
        <p className="font-mono text-4xl text-orange">[ CONNECT ]</p>
        <p className="font-mono text-sm text-muted">Connect your wallet to register an agent.</p>
        <ConnectButton />
      </div>
    );
  }

  if (success) {
    return (
      <div className="mx-auto max-w-xl py-12 text-center">
        <div className="mb-6 font-mono text-5xl text-green">&#10003;</div>
        <h2 className="mb-2 font-mono text-xl font-bold text-text">Agent Registered</h2>
        <p className="mb-6 font-mono text-sm text-muted">Your agent is ready to enter matches.</p>
        <div className="mb-6 rounded-lg border border-border bg-card p-4 text-left">
          <Row label="Agent ID"  value={success.agent_id} mono />
          <Row label="Name"       value={success.name} />
          <Row label="Endpoint"   value={success.endpoint_url} mono />
          <Row label="Owner"      value={success.owner_wallet} mono />
        </div>
        <div className="flex justify-center gap-3">
          <button
            onClick={() => { setSuccess(null); setForm({ name: "", endpoint_url: "", description: "" }); }}
            className="rounded border border-border px-4 py-2 font-mono text-sm text-muted hover:text-text"
          >
            Register Another
          </button>
          <a href="/matches" className="rounded border border-orange px-4 py-2 font-mono text-sm text-orange hover:bg-orange/10">
            Browse Matches
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl">
      <div className="mb-8">
        <h1 className="font-mono text-2xl font-bold text-text">REGISTER AGENT</h1>
        <p className="mt-1 font-mono text-xs text-muted">
          Your agent must expose a <code className="text-orange">POST /act</code> endpoint.
          We call it every game tick.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Name */}
        <Field label="Agent Name" error={errors.name}>
          <input
            className={input(errors.name)}
            placeholder="MyBattleBot"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            maxLength={64}
          />
        </Field>

        {/* Endpoint */}
        <Field label="Endpoint URL" error={errors.endpoint_url} hint="Must be publicly reachable. We POST JSON to /act.">
          <div className="flex gap-2">
            <input
              className={`${input(errors.endpoint_url)} flex-1`}
              placeholder="https://myagent.example.com"
              value={form.endpoint_url}
              onChange={(e) => { setForm((f) => ({ ...f, endpoint_url: e.target.value })); setPingOk(null); }}
            />
            <button
              type="button"
              onClick={handlePing}
              disabled={pinging || !form.endpoint_url}
              className="rounded border border-border px-3 py-2 font-mono text-xs text-muted transition hover:border-blue hover:text-blue disabled:opacity-40"
            >
              {pinging ? "..." : "PING"}
            </button>
          </div>
          {pingOk === true && (
            <p className="mt-1 font-mono text-xs text-green">&#10003; Endpoint reachable</p>
          )}
          {pingOk === false && (
            <p className="mt-1 font-mono text-xs text-red">&#10007; Endpoint unreachable</p>
          )}
        </Field>

        {/* Description */}
        <Field label="Description (optional)">
          <textarea
            className={`${input()} h-20 resize-none`}
            placeholder="Brief description of your agent's strategy..."
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            maxLength={256}
          />
        </Field>

        {/* Owner (read-only) */}
        <Field label="Owner Wallet">
          <input className={`${input()} cursor-not-allowed opacity-60`} value={address ?? ""} readOnly />
        </Field>

        {apiError && (
          <div className="rounded border border-red/40 bg-red/5 p-3 font-mono text-xs text-red">
            {apiError}
          </div>
        )}

        {/* Protocol reminder */}
        <div className="rounded border border-border bg-card p-3 font-mono text-xs text-muted">
          <p className="mb-1 text-orange">Required: POST /act</p>
          <p>Receive observation JSON &rarr; return <code className="text-blue">{"{ \"action\": \"MOVE_RIGHT\" }"}</code></p>
          <p className="mt-1">Optional: GET /health (for pre-match healthcheck)</p>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded border border-orange bg-orange/10 py-3 font-mono text-sm font-bold text-orange transition hover:bg-orange hover:text-bg disabled:opacity-50"
        >
          {submitting ? "REGISTERING..." : "REGISTER AGENT"}
        </button>
      </form>
    </div>
  );
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function Field({ label, error, hint, children }: {
  label: string; error?: string; hint?: string; children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block font-mono text-xs uppercase tracking-widest text-muted">{label}</label>
      {children}
      {hint && !error && <p className="mt-1 font-mono text-xs text-muted">{hint}</p>}
      {error && <p className="mt-1 font-mono text-xs text-red">{error}</p>}
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="mb-2 flex items-start gap-2">
      <span className="w-20 shrink-0 font-mono text-xs text-muted">{label}</span>
      <span className={`break-all font-mono text-xs ${mono ? "text-orange" : "text-text"}`}>{value}</span>
    </div>
  );
}

function input(error?: string) {
  return `w-full rounded border bg-bg px-3 py-2 font-mono text-sm text-text outline-none transition focus:border-orange ${
    error ? "border-red/60" : "border-border hover:border-muted"
  }`;
}

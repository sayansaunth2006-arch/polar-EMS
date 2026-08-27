"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Snowflake, Loader2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useAuthStore, type Role } from "@/lib/store";

const DEMO_ACCOUNTS: { label: string; email: string; password: string }[] = [
  { label: "Station Energy Operator", email: "operator@polar-ems.demo", password: "operator123" },
  { label: "Station Administrator", email: "admin@polar-ems.demo", password: "admin123" },
  { label: "Research Scientist", email: "scientist@polar-ems.demo", password: "scientist123" },
];

export default function LoginPage() {
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(email, password);
      setSession({ token: res.access_token, role: res.role as Role, fullName: res.full_name, email });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg border border-border bg-surface text-accent">
            <Snowflake className="h-6 w-6" />
          </div>
          <h1 className="text-lg font-semibold tracking-wide text-foreground">POLAR-EMS</h1>
          <p className="text-xs text-muted">AI-Driven Energy Management for Polar Research Stations</p>
        </div>

        <form onSubmit={handleSubmit} className="rounded-lg border border-border bg-surface p-5">
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-muted">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-accent"
                placeholder="operator@polar-ems.demo"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-muted">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-accent"
                placeholder="••••••••"
              />
            </div>
          </div>

          {error && <p className="mt-3 rounded-md border border-status-critical/30 bg-[var(--status-critical-bg)] px-3 py-2 text-xs text-status-critical">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-md bg-accent px-3 py-2 text-sm font-semibold text-[#04141d] hover:bg-accent/90 disabled:opacity-60"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Sign in
          </button>
        </form>

        <div className="mt-4 rounded-lg border border-border bg-surface p-4">
          <p className="mb-2 text-xs font-medium text-muted">Demo accounts (synthetic data)</p>
          <div className="space-y-1.5">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                type="button"
                onClick={() => {
                  setEmail(acc.email);
                  setPassword(acc.password);
                }}
                className="flex w-full items-center justify-between rounded-md border border-border-strong bg-surface-raised px-2.5 py-1.5 text-left text-xs hover:bg-border"
              >
                <span className="text-foreground">{acc.label}</span>
                <span className="font-data text-muted">{acc.email}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

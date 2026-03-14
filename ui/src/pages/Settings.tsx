import { CheckCircle, XCircle } from "lucide-react";
import { useKeys, useProviders } from "../api/hooks";

export default function Settings() {
  const { data, isLoading } = useProviders();
  const keys = useKeys();

  if (isLoading || !data) {
    return <div>Loading settings...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-6">
        <div className="text-sm font-semibold">Providers</div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {data.providers.map((provider) => (
            <div key={provider.provider} className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
              <div className="text-sm font-medium capitalize">{provider.provider}</div>
              {provider.enabled ? (
                <CheckCircle size={18} className="text-[var(--success)]" />
              ) : (
                <XCircle size={18} className="text-[var(--danger)]" />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-6">
        <div className="text-sm font-semibold">Rate Limits</div>
        <div className="mt-3 text-lg">{data.rate_limit_rpm} requests/minute</div>
        <div className="text-sm text-[var(--muted)]">Read-only for MVP</div>
      </div>

      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-6">
        <div className="text-sm font-semibold">API Key Prefixes</div>
        <div className="mt-3 text-sm text-[var(--muted)]">Manage full keys on the API Keys page.</div>
        <div className="mt-4 flex flex-wrap gap-2">
          {keys.data?.map((key) => (
            <span key={key.id} className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-3 py-1 text-xs">
              {key.key_prefix}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

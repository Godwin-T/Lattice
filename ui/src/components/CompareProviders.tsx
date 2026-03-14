import { useMemo, useState } from "react";
import { usePricing, CompareResponseItem } from "../api/hooks";

const DEFAULT_PROMPT = "Hello from LatticeAI";
const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function CompareProviders({ apiKey }: { apiKey: string }) {
  const pricingQuery = usePricing();
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [fallback, setFallback] = useState(true);
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
  const [results, setResults] = useState<CompareResponseItem[]>([]);

  const providerOptions = useMemo(() => {
    const items = pricingQuery.data || [];
    const providers = new Set<string>();
    items.forEach((item) => {
      if (item.active) providers.add(item.provider);
    });
    return Array.from(providers).sort();
  }, [pricingQuery.data]);

  const modelsByProvider = useMemo(() => {
    const map = new Map<string, string[]>();
    (pricingQuery.data || []).forEach((item) => {
      if (!item.active || item.model_type !== "chat") return;
      const list = map.get(item.provider) || [];
      if (!list.includes(item.model)) list.push(item.model);
      map.set(item.provider, list);
    });
    map.forEach((list) => list.sort());
    return map;
  }, [pricingQuery.data]);

  const handleCompare = async () => {
    const providers = providerOptions
      .map((provider) => ({ provider, model: selectedModels[provider] }))
      .filter((item) => item.model);

    if (!apiKey.trim() || !prompt.trim() || providers.length === 0) {
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/test/compare`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey.trim()}`
        },
        body: JSON.stringify({ prompt: prompt.trim(), providers, fallback })
      });
      const text = await res.text();
      if (!res.ok) {
        setResults([
          {
            provider: "all",
            model: "",
            status: "error",
            latency_ms: 0,
            prompt_tokens: 0,
            completion_tokens: 0,
            total_tokens: 0,
            cost_usd: 0,
            response: null,
            error_message: text || res.statusText
          }
        ]);
        return;
      }
      const data = text ? JSON.parse(text) : { items: [] };
      setResults(data.items || []);
    } catch (err: any) {
      setResults([
        {
          provider: "all",
          model: "",
          status: "error",
          latency_ms: 0,
          prompt_tokens: 0,
          completion_tokens: 0,
          total_tokens: 0,
          cost_usd: 0,
          response: null,
          error_message: err?.message || "Request failed"
        }
      ]);
    }
  };

  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-4 space-y-4">
      <div>
        <div className="text-sm font-semibold">Compare Providers</div>
        <div className="text-xs text-[var(--muted)]">Run the same prompt across providers to compare latency, output, and token usage.</div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-3 text-sm"
          rows={4}
        />
        <div className="space-y-3">
          {providerOptions.map((provider) => (
            <div key={provider} className="flex items-center gap-3">
              <div className="w-24 text-xs uppercase text-[var(--muted)]">{provider}</div>
              <select
                value={selectedModels[provider] || ""}
                onChange={(e) =>
                  setSelectedModels((prev) => ({
                    ...prev,
                    [provider]: e.target.value
                  }))
                }
                className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
              >
                <option value="">Select model</option>
                {(modelsByProvider.get(provider) || []).map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm text-[var(--muted)]">
          <input type="checkbox" checked={fallback} onChange={(e) => setFallback(e.target.checked)} />
          Enable fallback on provider failure
        </label>
        <button
          onClick={handleCompare}
          className="rounded-xl bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white"
        >
          Run Comparison
        </button>
      </div>

      {results.length > 0 && (
        <div className="overflow-auto rounded-2xl border border-[var(--border)]">
          <table className="min-w-full text-sm">
            <thead className="bg-[var(--surface-2)] text-left">
              <tr>
                <th className="px-4 py-3">Provider</th>
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3">Latency</th>
                <th className="px-4 py-3">Tokens</th>
                <th className="px-4 py-3">Cost</th>
                <th className="px-4 py-3">Response</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {results.map((item) => (
                <tr key={`${item.provider}-${item.model}`} className="border-t border-[var(--border)]">
                  <td className="px-4 py-3">{item.provider}</td>
                  <td className="px-4 py-3">{item.model}</td>
                  <td className="px-4 py-3">{item.latency_ms} ms</td>
                  <td className="px-4 py-3">{item.total_tokens}</td>
                  <td className="px-4 py-3">${item.cost_usd.toFixed(4)}</td>
                  <td className="px-4 py-3">
                    <div className="max-w-[320px] truncate" title={item.response || item.error_message || ""}>
                      {item.response || item.error_message || "—"}
                    </div>
                  </td>
                  <td className="px-4 py-3">{item.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { useKeys, usePricing, useProviders } from "../api/hooks";
import CompareProviders from "../components/CompareProviders";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function TestKeys() {
  const keysQuery = useKeys();
  const [apiKey, setApiKey] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const providersQuery = useProviders();
  const pricingQuery = usePricing();
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("");
  const [prompt, setPrompt] = useState("Hello from LatticeAI");
  const [fallback, setFallback] = useState(true);
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [providerUsed, setProviderUsed] = useState<string | null>(null);
  const [fallbackUsed, setFallbackUsed] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);

  const providerOptions = useMemo(() => {
    const items = pricingQuery.data || [];
    const providers = new Set<string>();
    items.forEach((item) => {
      if (item.active) providers.add(item.provider);
    });
    return Array.from(providers).sort();
  }, [pricingQuery.data]);

  useEffect(() => {
    if (providerOptions.length && !providerOptions.includes(provider)) {
      setProvider(providerOptions[0]);
      setModel("");
    }
  }, [providerOptions, provider]);

  const modelOptions = useMemo(() => {
    const items = pricingQuery.data || [];
    return items
      .filter((item) => item.active && item.model_type === "chat" && (!provider || item.provider === provider))
      .map((item) => item.model);
  }, [pricingQuery.data, provider]);

  const tagOptions = useMemo(() => {
    const tags = new Set<string>();
    (keysQuery.data || []).forEach((key) => {
      if (key.tag) tags.add(key.tag);
    });
    return Array.from(tags).sort();
  }, [keysQuery.data]);

  const tagToPrefix = useMemo(() => {
    const map = new Map<string, string>();
    (keysQuery.data || []).forEach((key) => {
      if (key.tag && key.key_prefix) {
        map.set(key.tag, key.key_prefix);
      }
    });
    return map;
  }, [keysQuery.data]);

  const handleTest = async () => {
    setError(null);
    setResponse(null);
    setProviderUsed(null);
    setFallbackUsed(null);
    if (!apiKey.trim()) {
      setError("Paste a full API key.");
      return;
    }
    if (!model.trim()) {
      setError("Provide a model name.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/v1/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey.trim()}`
        },
        body: JSON.stringify({
          model: model.trim(),
          provider,
          fallback,
          messages: [{ role: "user", content: prompt }]
        })
      });

      const text = await res.text();
      if (!res.ok) {
        setError(text || res.statusText);
        return;
      }
      const data = text ? JSON.parse(text) : {};
      const content = data?.choices?.[0]?.message?.content ?? JSON.stringify(data, null, 2);
      setResponse(content);
      setProviderUsed(res.headers.get("X-Provider-Used"));
      setFallbackUsed(res.headers.get("X-Provider-Fallback") === "true");
    } catch (err: any) {
      setError(err?.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="text-lg font-semibold">Test API Keys</div>
        <div className="text-sm text-[var(--muted)]">Send a test request through the LatticeAI gateway.</div>
      </div>

      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-4 space-y-4">
        <div className="grid gap-3 md:grid-cols-3">
          <select
            value={tagFilter}
            onChange={(e) => {
              setTagFilter(e.target.value);
            }}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
          >
            <option value="">All tags</option>
            {tagOptions.map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>
          <input
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={tagFilter ? `Paste full API key for ${tagFilter} (${tagToPrefix.get(tagFilter) || "prefix"})` : "Paste full API key"}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
          />

          <select
            value={provider}
            onChange={(e) => {
              setProvider(e.target.value);
              setModel("");
            }}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
          >
            {providerOptions.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>

          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
          >
            <option value="">Select model</option>
            {modelOptions.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        <div>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface)] p-3 text-sm"
            rows={4}
          />
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-[var(--muted)]">
            <input type="checkbox" checked={fallback} onChange={(e) => setFallback(e.target.checked)} />
            Enable fallback on provider failure
          </label>
          <button
            onClick={handleTest}
            className="rounded-xl bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white"
            disabled={loading}
          >
            {loading ? "Testing..." : "Run Test"}
          </button>
        </div>
        {error && <div className="text-sm text-[var(--danger)]">{error}</div>}
      </div>

      {(response || providerUsed) && (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-4 space-y-2">
          <div className="text-sm font-semibold">Response</div>
          {providerUsed && (
            <div className="text-xs text-[var(--muted)]">
              Provider used: {providerUsed}
              {fallbackUsed !== null && ` (fallback ${fallbackUsed ? "enabled" : "not used"})`}
            </div>
          )}
          <pre className="whitespace-pre-wrap text-sm bg-[var(--surface)] border border-[var(--border)] rounded-xl p-3">
            {response}
          </pre>
        </div>
      )}

      <CompareProviders apiKey={apiKey} />
    </div>
  );
}

import { useMemo, useState } from "react";
import { ModelPricing, useCreatePricing, useDeletePricing, usePricing, useUpdatePricing } from "../api/hooks";

const PROVIDERS = ["openai", "groq", "anthropic"];
const MODEL_TYPES = ["chat", "embedding"];

export default function Pricing() {
  const pricing = usePricing();
  const createPricing = useCreatePricing();
  const updatePricing = useUpdatePricing();
  const deletePricing = useDeletePricing();

  const [provider, setProvider] = useState(PROVIDERS[0]);
  const [model, setModel] = useState("");
  const [modelType, setModelType] = useState(MODEL_TYPES[0]);
  const [cost, setCost] = useState("");
  const [active, setActive] = useState(true);
  const [drafts, setDrafts] = useState<Record<string, Partial<ModelPricing>>>({});
  const [error, setError] = useState<string | null>(null);

  const items = useMemo(() => pricing.data || [], [pricing.data]);

  const handleCreate = () => {
    setError(null);
    if (!model.trim()) {
      setError("Model name is required.");
      return;
    }
    const costValue = Number(cost);
    if (Number.isNaN(costValue) || costValue < 0) {
      setError("Cost per 1M tokens must be a non-negative number.");
      return;
    }
    createPricing.mutate(
      {
        provider,
        model: model.trim(),
        model_type: modelType,
        cost_per_1m_tokens: costValue,
        active
      },
      {
        onSuccess: () => {
          setModel("");
          setCost("");
          setActive(true);
          pricing.refetch();
        }
      }
    );
  };

  const setDraft = (id: string, key: keyof ModelPricing, value: string | boolean) => {
    setDrafts((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        [key]: value
      }
    }));
  };

  const handleSave = (id: string) => {
    const draft = drafts[id];
    if (!draft) return;
    const payload: Partial<ModelPricing> = { ...draft } as Partial<ModelPricing>;
    if (payload.cost_per_1m_tokens !== undefined) {
      const value = Number(payload.cost_per_1m_tokens);
      if (Number.isNaN(value) || value < 0) {
        setError("Cost per 1M tokens must be a non-negative number.");
        return;
      }
      payload.cost_per_1m_tokens = value;
    }
    updatePricing.mutate(
      { id, ...payload },
      {
        onSuccess: () => {
          setDrafts((prev) => ({ ...prev, [id]: {} }));
          pricing.refetch();
        }
      }
    );
  };

  const handleDelete = (id: string) => {
    deletePricing.mutate(id, {
      onSuccess: () => pricing.refetch()
    });
  };

  if (pricing.isLoading || !pricing.data) {
    return <div>Loading pricing...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="text-lg font-semibold">Pricing & Models</div>
        <div className="text-sm text-[var(--muted)]">Manage provider models and cost per 1M tokens.</div>
      </div>

      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
        <div className="text-sm font-semibold">Add model pricing</div>
        <div className="mt-3 grid gap-3 md:grid-cols-5">
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
          >
            {PROVIDERS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="Model name"
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
          />
          <select
            value={modelType}
            onChange={(e) => setModelType(e.target.value)}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
          >
            {MODEL_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <input
            value={cost}
            onChange={(e) => setCost(e.target.value)}
            placeholder="Cost per 1M tokens"
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
          />
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-[var(--muted)]">
              <input
                type="checkbox"
                checked={active}
                onChange={(e) => setActive(e.target.checked)}
              />
              Active
            </label>
            <button
              onClick={handleCreate}
              className="rounded-xl bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white"
            >
              Add
            </button>
          </div>
        </div>
        {error && <div className="mt-2 text-sm text-[var(--danger)]">{error}</div>}
      </div>

      <div className="overflow-auto rounded-2xl border border-[var(--border)]">
        <table className="min-w-full text-sm">
          <thead className="bg-[var(--surface-2)] text-left">
            <tr>
              <th className="px-4 py-3">Provider</th>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Cost / 1M</th>
              <th className="px-4 py-3">Active</th>
              <th className="px-4 py-3">Updated</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t border-[var(--border)]">
                <td className="px-4 py-3">{item.provider}</td>
                <td className="px-4 py-3">{item.model}</td>
                <td className="px-4 py-3">{item.model_type}</td>
                <td className="px-4 py-3">
                  <input
                    defaultValue={item.cost_per_1m_tokens}
                    onChange={(e) => setDraft(item.id, "cost_per_1m_tokens", e.target.value)}
                    className="w-32 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-2 py-1 text-xs"
                  />
                </td>
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    defaultChecked={item.active}
                    onChange={(e) => setDraft(item.id, "active", e.target.checked)}
                  />
                </td>
                <td className="px-4 py-3 text-[var(--muted)]">{new Date(item.updated_at).toLocaleString()}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSave(item.id)}
                      className="rounded-lg border border-[var(--border)] px-3 py-1 text-xs"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="rounded-lg border border-[var(--border)] px-3 py-1 text-xs text-[var(--danger)]"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

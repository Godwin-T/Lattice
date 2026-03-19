import { useMemo, useState } from "react";
import { useCreateKey, useDeleteKey, useKeys, useProjects, useRevokeKey } from "../api/hooks";

export default function ApiKeys() {
  const keysQuery = useKeys();
  const projects = useProjects();
  const createKey = useCreateKey();
  const revokeKey = useRevokeKey();
  const deleteKey = useDeleteKey();
  const [newKey, setNewKey] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState("");
  const [tag, setTag] = useState("");
  const [error, setError] = useState<string | null>(null);

  const projectMap = useMemo(
    () => new Map((projects.data || []).map((project) => [project.id, project.name])),
    [projects.data]
  );

  const handleCreate = () => {
    setError(null);
    if (!selectedProject) {
      setError("Select a project to create a key.");
      return;
    }
    createKey.mutate(
      { project_id: selectedProject, tag: tag.trim() || null },
      {
      onSuccess: (data) => {
        setNewKey(data.key);
        keysQuery.refetch();
        setSelectedProject("");
        setTag("");
      }
      }
    );
  };

  const handleRevoke = (id: string) => {
    revokeKey.mutate(id, {
      onSuccess: () => keysQuery.refetch()
    });
  };

  const handleDelete = (id: string, keyPrefix: string) => {
    const confirmed = window.confirm(
      `Delete API key ${keyPrefix}? This will permanently remove the key and all usage logs tied to it. This cannot be undone.`
    );
    if (!confirmed) return;
    deleteKey.mutate(id, {
      onSuccess: () => keysQuery.refetch()
    });
  };

  if (keysQuery.isLoading || !keysQuery.data) {
    return <div>Loading API keys...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-lg font-semibold">API Keys</div>
          <div className="text-sm text-[var(--muted)]">Create and manage your gateway API keys.</div>
        </div>
      </div>

      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
        <div className="text-sm font-semibold">Create a new key</div>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
          >
            <option value="">Select project</option>
            {(projects.data || []).map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
          <input
            value={tag}
            onChange={(e) => setTag(e.target.value)}
            placeholder="Tag (optional)"
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
          />
          <button
            onClick={handleCreate}
            className="rounded-xl bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white"
          >
            Create Key
          </button>
        </div>
        {error && <div className="mt-2 text-sm text-[var(--danger)]">{error}</div>}
      </div>

      {newKey && (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
          <div className="text-sm font-semibold">New API Key</div>
          <div className="mt-2 break-all rounded-xl border border-[var(--border)] bg-[var(--surface)] p-3 text-sm">
            {newKey}
          </div>
          <div className="mt-2 text-xs text-[var(--muted)]">Copy this key now. You won’t see it again.</div>
        </div>
      )}

      <div className="overflow-auto rounded-2xl border border-[var(--border)]">
        <table className="min-w-full text-sm">
          <thead className="bg-[var(--surface-2)] text-left">
            <tr>
              <th className="px-4 py-3">Prefix</th>
              <th className="px-4 py-3">Tag</th>
              <th className="px-4 py-3">Project</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3">Last Used</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {keysQuery.data.map((key) => (
              <tr key={key.id} className="border-t border-[var(--border)]">
                <td className="px-4 py-3">{key.key_prefix}</td>
                <td className="px-4 py-3">{key.tag || "—"}</td>
                <td className="px-4 py-3">{projectMap.get(key.project_id) || "Unknown"}</td>
                <td className="px-4 py-3 capitalize">{key.status}</td>
                <td className="px-4 py-3 text-[var(--muted)]">{new Date(key.created_at).toLocaleString()}</td>
                <td className="px-4 py-3 text-[var(--muted)]">
                  {key.last_used_at ? new Date(key.last_used_at).toLocaleString() : "—"}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button
                      className="rounded-lg border border-[var(--border)] px-3 py-1 text-xs"
                      onClick={() => handleRevoke(key.id)}
                    >
                      Revoke
                    </button>
                    <button
                      className="rounded-lg border border-[var(--border)] px-3 py-1 text-xs text-[var(--danger)]"
                      onClick={() => handleDelete(key.id, key.key_prefix)}
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

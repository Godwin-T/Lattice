import { useEffect, useMemo, useState } from "react";
import { useKeys, useProjects, useRequests } from "../api/hooks";
import Badge from "../components/Badge";

export default function Requests() {
  const [projectId, setProjectId] = useState("");
  const [keyId, setKeyId] = useState("");
  const { data, isLoading } = useRequests({
    projectId: projectId || undefined,
    keyId: keyId || undefined
  });
  const projects = useProjects();
  const keys = useKeys();

  const projectMap = useMemo(
    () => new Map((projects.data || []).map((project) => [project.id, project.name])),
    [projects.data]
  );
  const keyMap = useMemo(
    () => new Map((keys.data || []).map((key) => [key.id, key.key_prefix])),
    [keys.data]
  );
  const keyOptions = useMemo(() => {
    const allKeys = keys.data || [];
    if (projectId) {
      return allKeys.filter((key) => key.project_id === projectId);
    }
    return allKeys;
  }, [keys.data, projectId]);

  useEffect(() => {
    if (!projectId || !keyId) return;
    const valid = (keys.data || []).some((key) => key.id === keyId && key.project_id === projectId);
    if (!valid) {
      setKeyId("");
    }
  }, [projectId, keyId, keys.data]);

  if (isLoading || !data) {
    return <div>Loading requests...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
        >
          <option value="">All projects</option>
          {(projects.data || []).map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
        <select
          value={keyId}
          onChange={(e) => setKeyId(e.target.value)}
          className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
        >
          <option value="">All keys</option>
          {keyOptions.map((key) => (
            <option key={key.id} value={key.id}>
              {key.key_prefix}
            </option>
          ))}
        </select>
      </div>

      <div className="overflow-auto rounded-2xl border border-[var(--border)]">
        <table className="min-w-full text-sm">
          <thead className="bg-[var(--surface-2)] text-left">
            <tr>
              <th className="px-4 py-3">Time</th>
              <th className="px-4 py-3">Project</th>
              <th className="px-4 py-3">Key</th>
              <th className="px-4 py-3">Owner</th>
              <th className="px-4 py-3">Provider</th>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Latency</th>
              <th className="px-4 py-3">Cost</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={item.id} className="border-t border-[var(--border)]">
                <td className="px-4 py-3 text-[var(--muted)]">{new Date(item.created_at).toLocaleString()}</td>
                <td className="px-4 py-3">{projectMap.get(item.project_id) || "Unknown"}</td>
                <td className="px-4 py-3">{(item.api_key_id && keyMap.get(item.api_key_id)) || "—"}</td>
                <td className="px-4 py-3">{item.owner_user_id ? "Admin" : "Unassigned"}</td>
                <td className="px-4 py-3"><Badge label={item.provider} /></td>
                <td className="px-4 py-3">{item.model}</td>
                <td className="px-4 py-3">{item.status}</td>
                <td className="px-4 py-3">{item.latency_ms} ms</td>
                <td className="px-4 py-3">${item.cost_usd.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

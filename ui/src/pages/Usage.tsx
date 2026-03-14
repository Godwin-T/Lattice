import { useMemo, useState } from "react";
import { useProjects, useUsageByKey, useUsageByProject, useUsageByUser, useUsageOverview } from "../api/hooks";

export default function Usage() {
  const overview = useUsageOverview();
  const byUser = useUsageByUser();
  const byProject = useUsageByProject();
  const projects = useProjects();
  const [selectedProject, setSelectedProject] = useState<string | undefined>(undefined);
  const byKey = useUsageByKey(selectedProject);

  const projectOptions = useMemo(() => projects.data || [], [projects.data]);

  if (overview.isLoading || !overview.data) {
    return <div>Loading usage...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
          <div className="text-xs uppercase text-[var(--muted)]">Total Requests</div>
          <div className="mt-2 text-2xl font-semibold">{overview.data.total_requests}</div>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
          <div className="text-xs uppercase text-[var(--muted)]">Total Cost</div>
          <div className="mt-2 text-2xl font-semibold">${overview.data.total_cost_usd.toFixed(2)}</div>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
          <div className="text-xs uppercase text-[var(--muted)]">Total Tokens</div>
          <div className="mt-2 text-2xl font-semibold">{overview.data.total_tokens}</div>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
          <div className="text-xs uppercase text-[var(--muted)]">Avg Latency</div>
          <div className="mt-2 text-2xl font-semibold">{overview.data.avg_latency_ms.toFixed(0)} ms</div>
        </div>
      </div>

      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-6">
        <div className="text-sm font-semibold">Usage by User</div>
        <div className="mt-4 overflow-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left">
              <tr>
                <th className="px-3 py-2">User</th>
                <th className="px-3 py-2">Requests</th>
                <th className="px-3 py-2">Tokens</th>
                <th className="px-3 py-2">Cost</th>
                <th className="px-3 py-2">Avg Latency</th>
              </tr>
            </thead>
            <tbody>
              {byUser.data?.items.map((item) => (
                <tr key={item.user_id ?? "unknown"} className="border-t border-[var(--border)]">
                  <td className="px-3 py-2">{item.email || "Admin"}</td>
                  <td className="px-3 py-2">{item.requests}</td>
                  <td className="px-3 py-2">{item.tokens}</td>
                  <td className="px-3 py-2">${item.cost_usd.toFixed(2)}</td>
                  <td className="px-3 py-2">{item.avg_latency_ms.toFixed(0)} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-6">
        <div className="text-sm font-semibold">Usage by Project</div>
        <div className="mt-4 overflow-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left">
              <tr>
                <th className="px-3 py-2">Project</th>
                <th className="px-3 py-2">Requests</th>
                <th className="px-3 py-2">Tokens</th>
                <th className="px-3 py-2">Cost</th>
                <th className="px-3 py-2">Avg Latency</th>
              </tr>
            </thead>
            <tbody>
              {byProject.data?.items.map((item) => (
                <tr key={item.project_id} className="border-t border-[var(--border)]">
                  <td className="px-3 py-2">{item.project_name}</td>
                  <td className="px-3 py-2">{item.requests}</td>
                  <td className="px-3 py-2">{item.tokens}</td>
                  <td className="px-3 py-2">${item.cost_usd.toFixed(2)}</td>
                  <td className="px-3 py-2">{item.avg_latency_ms.toFixed(0)} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-6">
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold">Usage by API Key</div>
          <select
            value={selectedProject || ""}
            onChange={(e) => setSelectedProject(e.target.value || undefined)}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
          >
            <option value="">Select project</option>
            {projectOptions.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>
        <div className="mt-4 overflow-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left">
              <tr>
                <th className="px-3 py-2">Key Prefix</th>
                <th className="px-3 py-2">Owner</th>
                <th className="px-3 py-2">Requests</th>
                <th className="px-3 py-2">Tokens</th>
                <th className="px-3 py-2">Cost</th>
                <th className="px-3 py-2">Avg Latency</th>
              </tr>
            </thead>
            <tbody>
              {byKey.data?.items.map((item) => (
                <tr key={item.api_key_id} className="border-t border-[var(--border)]">
                  <td className="px-3 py-2">{item.key_prefix}</td>
                  <td className="px-3 py-2">{item.owner_user_id ? "Admin" : "Unassigned"}</td>
                  <td className="px-3 py-2">{item.requests}</td>
                  <td className="px-3 py-2">{item.tokens}</td>
                  <td className="px-3 py-2">${item.cost_usd.toFixed(2)}</td>
                  <td className="px-3 py-2">{item.avg_latency_ms.toFixed(0)} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

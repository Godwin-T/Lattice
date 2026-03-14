import { useMemo, useState } from "react";
import { useCreateProject, useProjects, useUpdateProject } from "../api/hooks";

export default function Projects() {
  const projects = useProjects();
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const [newName, setNewName] = useState("");
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const projectList = useMemo(() => projects.data || [], [projects.data]);

  const handleCreate = () => {
    setError(null);
    if (!newName.trim()) {
      setError("Project name is required.");
      return;
    }
    createProject.mutate(
      { name: newName.trim() },
      {
        onSuccess: () => {
          setNewName("");
          projects.refetch();
        }
      }
    );
  };

  const handleUpdate = (projectId: string) => {
    setError(null);
    const fallback = projectList.find((project) => project.id === projectId)?.name || "";
    const name = (editing[projectId] ?? fallback).trim();
    if (!name) {
      setError("Project name is required.");
      return;
    }
    updateProject.mutate(
      { projectId, name },
      {
        onSuccess: () => projects.refetch()
      }
    );
  };

  if (projects.isLoading || !projects.data) {
    return <div>Loading projects...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="text-lg font-semibold">Projects</div>
        <div className="text-sm text-[var(--muted)]">Organize API keys and usage by project.</div>
      </div>

      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-4">
        <div className="text-sm font-semibold">Create project</div>
        <div className="mt-3 flex flex-wrap gap-3">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Project name"
            className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
          />
          <button
            onClick={handleCreate}
            className="rounded-xl bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white"
          >
            Create
          </button>
        </div>
        {error && <div className="mt-2 text-sm text-[var(--danger)]">{error}</div>}
      </div>

      <div className="rounded-2xl border border-[var(--border)]">
        <table className="min-w-full text-sm">
          <thead className="bg-[var(--surface-2)] text-left">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {projectList.map((project) => (
              <tr key={project.id} className="border-t border-[var(--border)]">
                <td className="px-4 py-3">
                  <input
                    value={editing[project.id] ?? project.name}
                    onChange={(e) =>
                      setEditing((prev) => ({
                        ...prev,
                        [project.id]: e.target.value
                      }))
                    }
                    className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
                  />
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => handleUpdate(project.id)}
                    className="rounded-lg border border-[var(--border)] px-3 py-1 text-xs"
                  >
                    Save
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

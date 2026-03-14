import ThemeToggle from "./ThemeToggle";

export default function Topbar() {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-[var(--border)] bg-[var(--surface)] px-6 py-4 shadow-[var(--shadow)]">
      <div>
        <div className="text-xs uppercase tracking-widest text-[var(--muted)]">LatticeAI Gateway</div>
        <div className="text-lg font-semibold">Dashboard</div>
      </div>
      <ThemeToggle />
    </div>
  );
}

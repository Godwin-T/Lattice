export default function Badge({ label }: { label: string }) {
  return (
    <span className="rounded-full border border-[var(--border)] bg-[var(--surface-2)] px-2 py-1 text-xs">
      {label}
    </span>
  );
}

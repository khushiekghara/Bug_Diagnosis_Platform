export default function StatCard({ label, value, icon: Icon, tone = "primary" }) {
  const toneClass = {
    primary: "bg-[var(--primary-soft)] text-[var(--primary)]",
    amber: "bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
    blue: "bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300",
    green: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
  }[tone];

  return (
    <div className="card rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-[var(--muted)]">{label}</p>
          <p className="mt-3 text-2xl font-semibold tracking-tight">{value}</p>
        </div>

        <div className={`grid h-9 w-9 place-items-center rounded-lg ${toneClass}`}>
          <Icon size={17} />
        </div>
      </div>
    </div>
  );
}
import { Bug, FilePlus2, LayoutDashboard, ListChecks, X } from "lucide-react";
import { NavLink } from "react-router-dom";

const items = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/submit", label: "Submit Bug", icon: FilePlus2 },
  { to: "/bugs", label: "Bug Reports", icon: ListChecks },
];

export default function Sidebar({ open, onClose }) {
  return (
    <aside
      className={[
        "fixed inset-y-0 left-0 z-50 w-64 border-r border-[var(--border)]",
        "bg-[var(--surface)] transition-transform duration-200",
        "lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full",
      ].join(" ")}
    >
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-5">
          <NavLink to="/dashboard" onClick={onClose} className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-lg bg-[var(--primary)] text-white">
              <Bug size={19} />
            </div>
            <div>
              <div className="text-[15px] font-semibold tracking-tight">BugDiag</div>
              <div className="text-[11px] text-[var(--muted)]">Diagnosis Platform</div>
            </div>
          </NavLink>

          <button
            onClick={onClose}
            className="rounded-lg p-2 text-[var(--muted)] hover:bg-[var(--surface-2)] lg:hidden"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-4 pt-7">
          <p className="mb-3 px-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
            Workspace
          </p>

          <nav className="space-y-1">
            {items.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                onClick={onClose}
                className={({ isActive }) =>
                  [
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition",
                    isActive
                      ? "bg-[var(--primary-soft)] font-medium text-[var(--primary)]"
                      : "text-[var(--muted)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]",
                  ].join(" ")
                }
              >
                <Icon size={17} strokeWidth={1.8} />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="mt-auto p-4">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] p-3">
            <div className="mb-1 flex items-center gap-2 text-xs font-medium">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              FastAPI Backend
            </div>
            <p className="text-[11px] text-[var(--muted)]">localhost:8000</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
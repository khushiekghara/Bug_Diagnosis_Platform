import { ArrowUpRight, FileText, ClipboardPaste } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { formatDate } from "../utils/helpers";
import { StatusBadge } from "./StatusBadge";

export default function BugTable({ bugs = [], compact = false }) {
  const navigate = useNavigate();

  if (!bugs.length) {
    return (
      <div className="px-6 py-12 text-center">
        <p className="text-sm font-medium">No bug reports found</p>
        <p className="mt-1 text-xs text-[var(--muted)]">
          Submit a bug to start the diagnosis workflow.
        </p>
      </div>
    );
  }

  const visibleBugs = compact ? bugs.slice(0, 5) : bugs;

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left">
        <thead>
          <tr className="border-b border-[var(--border)] text-[10px] uppercase tracking-[0.12em] text-[var(--muted)]">
            <th className="px-5 py-3 font-medium">Bug</th>
            <th className="px-5 py-3 font-medium">Source</th>
            <th className="px-5 py-3 font-medium">Status</th>
            <th className="px-5 py-3 font-medium">Created</th>
            <th className="px-5 py-3 font-medium" />
          </tr>
        </thead>

        <tbody>
          {visibleBugs.map((bug) => (
            <tr
              key={bug.id}
              className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--surface-2)]/60"
            >
              <td className="px-5 py-4">
                <button
                  onClick={() => navigate(`/bugs/${bug.id}`)}
                  className="text-left"
                >
                  <p className="max-w-[360px] truncate text-sm font-medium">
                    {bug.title}
                  </p>
                  <p className="mt-1 text-[11px] text-[var(--muted)]">
                    BUG-{bug.id}
                  </p>
                </button>
              </td>

              <td className="px-5 py-4">
                <span className="inline-flex items-center gap-1.5 text-xs text-[var(--muted)]">
                  {bug.source_type === "file" ? (
                    <FileText size={14} />
                  ) : (
                    <ClipboardPaste size={14} />
                  )}
                  {bug.source_type === "file" ? "File" : "Paste"}
                </span>
              </td>

              <td className="px-5 py-4">
                <StatusBadge status={bug.status} />
              </td>

              <td className="px-5 py-4 text-xs text-[var(--muted)]">
                {formatDate(bug.created_at)}
              </td>

              <td className="px-5 py-4 text-right">
                <button
                  onClick={() => navigate(`/bugs/${bug.id}`)}
                  className="rounded-lg p-2 text-[var(--muted)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
                  title="View bug"
                >
                  <ArrowUpRight size={16} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
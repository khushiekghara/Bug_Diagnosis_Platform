import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import BugTable from "../components/BugTable";
import { api } from "../services/api";

export default function BugReports({ refreshKey }) {
  const [bugs, setBugs] = useState([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getBugs()
      .then(setBugs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [refreshKey]);

  const filtered = useMemo(() => {
    return bugs.filter((bug) => {
      const searchable = [
        bug.title,
        bug.description,
        bug.error_log,
        String(bug.id),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesQuery = searchable.includes(query.toLowerCase().trim());
      const matchesStatus = status === "all" || bug.status === status;

      return matchesQuery && matchesStatus;
    });
  }, [bugs, query, status]);

  return (
    <div className="space-y-6">
      <section>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--primary)]">
          History
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
          Bug Reports
        </h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Search and inspect reports submitted to the platform.
        </p>
      </section>

      <section className="card overflow-hidden rounded-xl">
        <div className="flex flex-col gap-3 border-b border-[var(--border)] p-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm font-semibold">
            {filtered.length} report{filtered.length === 1 ? "" : "s"}
          </p>

          <div className="flex gap-2">
            <div className="relative">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
              />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search bugs..."
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-2)] py-2 pl-9 pr-3 text-xs outline-none focus:border-[var(--primary)] sm:w-64"
              />
            </div>

            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 text-xs outline-none"
            >
              <option value="all">All status</option>
              <option value="analyzed">Analyzed</option>
              <option value="submitted">Submitted</option>
            </select>
          </div>
        </div>

        {error ? (
          <div className="p-6 text-sm text-[var(--danger)]">{error}</div>
        ) : loading ? (
          <div className="p-12 text-center text-sm text-[var(--muted)]">
            Loading bug reports...
          </div>
        ) : (
          <BugTable bugs={filtered} />
        )}
      </section>
    </div>
  );
}
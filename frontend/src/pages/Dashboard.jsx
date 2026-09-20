import { useEffect, useState } from "react";
import { AlertTriangle, Bug, CheckCircle2, Clock3 } from "lucide-react";
import { Link } from "react-router-dom";
import StatCard from "../components/StatCard";
import BugTable from "../components/BugTable";
import { api } from "../services/api";

export default function Dashboard({ refreshKey }) {
  const [bugs, setBugs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [highSeverity, setHighSeverity] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);

      try {
        const data = await api.getBugs();
        if (!active) return;

        setBugs(data);

        const analyzed = data.filter((bug) => bug.status === "analyzed");

        const diagnoses = await Promise.all(
          analyzed.map((bug) =>
            api.getDiagnosis(bug.id).catch(() => null)
          )
        );

        if (active) {
          setHighSeverity(
            diagnoses.filter((item) =>
              ["high", "critical"].includes(
                item?.severity?.toLowerCase()
              )
            ).length
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [refreshKey]);

  const analyzed = bugs.filter((bug) => bug.status === "analyzed").length;
  const submitted = bugs.filter((bug) => bug.status === "submitted").length;

  return (
    <div className="space-y-6">
      <section>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--primary)]">
          Overview
        </p>
        <div className="mt-2 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Bug Diagnosis Dashboard
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
              Review submitted bugs and the results produced by your diagnosis pipeline.
            </p>
          </div>

          <Link
            to="/submit"
            className="inline-flex items-center justify-center rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white transition hover:opacity-90"
          >
            Submit a bug
          </Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Bugs" value={bugs.length} icon={Bug} />
        <StatCard label="Analyzed" value={analyzed} icon={CheckCircle2} tone="green" />
        <StatCard label="Submitted" value={submitted} icon={Clock3} tone="amber" />
        <StatCard label="High Severity" value={highSeverity} icon={AlertTriangle} tone="amber" />
      </section>

      <section className="card overflow-hidden rounded-xl">
        <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
          <div>
            <h2 className="text-sm font-semibold">Recent Bug Reports</h2>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Latest reports received by the platform.
            </p>
          </div>

          <Link
            to="/bugs"
            className="text-xs font-medium text-[var(--primary)] hover:underline"
          >
            View all
          </Link>
        </div>

        {loading ? (
          <div className="px-6 py-12 text-center text-sm text-[var(--muted)]">
            Loading bug reports...
          </div>
        ) : (
          <BugTable bugs={bugs} compact />
        )}
      </section>
    </div>
  );
}
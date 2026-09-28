import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3,
  Copy,
  Layers,
  Repeat,
  RefreshCw,
  Tag,
} from "lucide-react";
import { api } from "../services/api";

export default function Analytics({ refreshKey }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setLoading(true);
      setError("");
      const report = await api.getAnalytics();
      setData(report);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [refreshKey]);

  if (loading && !data) {
    return <Message>Loading analytics...</Message>;
  }

  if (error) {
    return <Message>{error}</Message>;
  }

  if (!data || data.total_bugs_analyzed === 0) {
    return (
      <div className="space-y-6">
        <PageHeader onRefresh={load} loading={loading} />
        <Message>
          No analyzed bugs yet. Submit a few bug reports and pattern analytics
          will appear here.
        </Message>
      </div>
    );
  }

  const dup = data.duplicate_cluster_summary;

  return (
    <div className="space-y-6">
      <PageHeader onRefresh={load} loading={loading} />

      {/* --- Headline numbers --- */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatBox label="Bugs Submitted" value={data.total_bugs_submitted} />
        <StatBox label="Bugs Analyzed" value={data.total_bugs_analyzed} />
        <StatBox
          label="Repeat Bug Rate"
          value={`${dup.duplicate_rate_percent}%`}
          hint="duplicates + related issues"
        />
        <StatBox
          label="Systemic Patterns"
          value={data.recurring_patterns.length}
          hint="component + exception seen 2+ times"
        />
      </section>

      <div className="grid gap-5 xl:grid-cols-2">
        {/* --- High-frequency components --- */}
        <section className="card rounded-xl">
          <SectionHeader
            title="High-Frequency Affected Components"
            icon={<Layers size={15} />}
          />
          <div className="p-5">
            <BarList
              items={data.component_frequency.map((c) => ({
                label: c.component,
                count: c.count,
                percentage: c.percentage,
              }))}
              emptyText="No component data yet."
            />
          </div>
        </section>

        {/* --- Severity distribution --- */}
        <section className="card rounded-xl">
          <SectionHeader
            title="Severity Distribution"
            icon={<BarChart3 size={15} />}
          />
          <div className="p-5">
            <BarList
              items={data.severity_distribution.map((s) => ({
                label: s.severity,
                count: s.count,
                percentage: s.percentage,
              }))}
              emptyText="No severity data yet."
            />
          </div>
        </section>
      </div>

      {/* --- Systemic issue patterns --- */}
      <section className="card rounded-xl">
        <SectionHeader
          title="Systemic Issue Patterns"
          icon={<Repeat size={15} />}
        />
        <div className="space-y-3 p-5">
          <p className="text-xs text-[var(--muted)]">
            The same exception type appearing repeatedly in the same component
            usually points to one underlying weak spot, not isolated incidents.
          </p>

          {data.recurring_patterns.length === 0 ? (
            <EmptyNote text="No recurring component + exception patterns detected yet. Patterns appear once the same pair shows up in 2 or more bugs." />
          ) : (
            data.recurring_patterns.map((p, i) => (
              <div
                key={i}
                className="rounded-lg border border-[var(--border)] p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium">
                    {p.exception_type}{" "}
                    <span className="font-normal text-[var(--muted)]">
                      in {p.component}
                    </span>
                  </p>
                  <span className="rounded-full bg-rose-100 px-2.5 py-1 text-xs font-medium text-rose-700">
                    {p.occurrences} occurrences
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {p.bug_ids.map((id) => (
                    <Link
                      key={id}
                      to={`/diagnosis/${id}`}
                      className="rounded border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--primary)] hover:bg-[var(--surface-2)]"
                    >
                      BUG-{id}
                    </Link>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-2">
        {/* --- Recurring exception types --- */}
        <section className="card rounded-xl">
          <SectionHeader
            title="Recurring Exception Types"
            icon={<Repeat size={15} />}
          />
          <div className="p-5">
            {data.exception_frequency.length === 0 ? (
              <EmptyNote text="No exception types detected yet." />
            ) : (
              <div className="space-y-2">
                {data.exception_frequency.map((e) => (
                  <div
                    key={e.exception_type}
                    className="flex items-center justify-between rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                  >
                    <span>{e.exception_type}</span>
                    <span className="text-xs text-[var(--muted)]">
                      {e.count} bug{e.count === 1 ? "" : "s"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* --- Recurring themes --- */}
        <section className="card rounded-xl">
          <SectionHeader
            title="Recurring Bug Themes"
            icon={<Tag size={15} />}
          />
          <div className="p-5">
            {data.recurring_themes.length === 0 ? (
              <EmptyNote text="No recurring keywords yet. Themes appear once the same word shows up in 2 or more bug titles." />
            ) : (
              <div className="flex flex-wrap gap-2">
                {data.recurring_themes.map((t) => (
                  <span
                    key={t.keyword}
                    className="rounded-full border border-[var(--border)] bg-[var(--surface-2)] px-3 py-1 text-xs"
                  >
                    {t.keyword}{" "}
                    <span className="font-semibold text-[var(--primary)]">
                      {t.count}
                    </span>
                  </span>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>

      {/* --- Duplicate summary --- */}
      <section className="card rounded-xl">
        <SectionHeader
          title="Duplicate Detection Summary"
          icon={<Copy size={15} />}
        />
        <div className="grid gap-4 p-5 sm:grid-cols-3">
          <MiniStat label="Likely Duplicate" value={dup.likely_duplicate} />
          <MiniStat label="Related Issue" value={dup.related_issue} />
          <MiniStat label="New / Unmatched" value={dup.new_unmatched} />
        </div>
      </section>
    </div>
  );
}

function PageHeader({ onRefresh, loading }) {
  return (
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Defect Pattern Analytics
        </h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Recurring themes, high-frequency components, and systemic issue
          patterns across every submitted bug.
        </p>
      </div>
      <button
        onClick={onRefresh}
        disabled={loading}
        className="inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm font-medium hover:bg-[var(--surface-2)] disabled:opacity-60"
      >
        <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
        Refresh
      </button>
    </div>
  );
}

function SectionHeader({ title, icon }) {
  return (
    <div className="flex items-center border-b border-[var(--border)] px-5 py-4">
      <h2 className="flex items-center gap-2 text-sm font-semibold">
        {icon}
        {title}
      </h2>
    </div>
  );
}

function StatBox({ label, value, hint }) {
  return (
    <div className="card rounded-xl p-5">
      <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
        {label}
      </p>
      <p className="mt-3 text-2xl font-semibold text-[var(--primary)]">
        {value}
      </p>
      {hint && <p className="mt-1 text-[11px] text-[var(--muted)]">{hint}</p>}
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="rounded-lg border border-[var(--border)] p-4 text-center">
      <p className="text-xl font-semibold">{value}</p>
      <p className="mt-1 text-xs text-[var(--muted)]">{label}</p>
    </div>
  );
}

function BarList({ items, emptyText }) {
  if (!items || items.length === 0) {
    return <EmptyNote text={emptyText} />;
  }

  const max = Math.max(...items.map((i) => i.count), 1);

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.label}>
          <div className="mb-1 flex items-center justify-between text-xs">
            <span className="font-medium">{item.label}</span>
            <span className="text-[var(--muted)]">
              {item.count} ({item.percentage}%)
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--surface-2)]">
            <div
              className="h-full rounded-full bg-[var(--primary)]"
              style={{ width: `${(item.count / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyNote({ text }) {
  return (
    <p className="rounded-lg border border-dashed border-[var(--border)] p-4 text-sm text-[var(--muted)]">
      {text}
    </p>
  );
}

function Message({ children }) {
  return (
    <div className="card rounded-xl p-12 text-center text-sm text-[var(--muted)]">
      {children}
    </div>
  );
}
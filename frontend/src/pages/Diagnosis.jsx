import { useEffect, useState } from "react";
import { ArrowLeft, RotateCcw, ShieldAlert } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";
import { formatDate } from "../utils/helpers";
import { SeverityBadge } from "../components/StatusBadge";

export default function Diagnosis() {
  const { bugId } = useParams();
  const navigate = useNavigate();

  const [bug, setBug] = useState(null);
  const [diagnosis, setDiagnosis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rerunning, setRerunning] = useState(false);
  const [error, setError] = useState("");

  const loadDiagnosis = async () => {
    try {
      setLoading(true);
      setError("");

      const [bugData, diagnosisData] = await Promise.all([
        api.getBug(bugId),
        api.getDiagnosis(bugId),
      ]);

      setBug(bugData);
      setDiagnosis(diagnosisData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDiagnosis();
  }, [bugId]);

  const rerun = async () => {
    try {
      setRerunning(true);
      setError("");

      await api.rerunDiagnosis(bugId);
      await loadDiagnosis();
    } catch (err) {
      setError(err.message);
    } finally {
      setRerunning(false);
    }
  };

  if (loading) {
    return <Message>Loading diagnosis...</Message>;
  }

  if (error || !bug || !diagnosis) {
    return (
      <div className="space-y-4">
        <Link
          to="/bugs"
          className="inline-flex items-center gap-2 text-xs text-[var(--muted)] hover:text-[var(--text)]"
        >
          <ArrowLeft size={15} />
          Back to reports
        </Link>
        <Message>{error || "Diagnosis is not available."}</Message>
      </div>
    );
  }

  const confidence =
    typeof diagnosis.confidence === "number"
      ? `${Math.round(diagnosis.confidence * 100)}%`
      : "—";

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <Link
            to={`/bugs/${bug.id}`}
            className="mb-3 inline-flex items-center gap-2 text-xs text-[var(--muted)] hover:text-[var(--text)]"
          >
            <ArrowLeft size={15} />
            Back to bug
          </Link>

          <p className="text-xs text-[var(--muted)]">BUG-{bug.id}</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            {bug.title}
          </h1>
          <p className="mt-2 text-xs text-[var(--muted)]">
            Analyzed {formatDate(diagnosis.analyzed_at)}
          </p>
        </div>

        <button
          onClick={rerun}
          disabled={rerunning}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm font-medium hover:bg-[var(--surface-2)] disabled:opacity-60"
        >
          <RotateCcw size={15} className={rerunning ? "animate-spin" : ""} />
          {rerunning ? "Running agents..." : "Re-run diagnosis"}
        </button>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <InfoCard label="Severity">
          <SeverityBadge severity={diagnosis.severity} />
        </InfoCard>

        <InfoCard label="Priority">
          {diagnosis.priority || "Not available"}
        </InfoCard>

        <InfoCard label="Affected Component">
          {diagnosis.affected_component || "Not available"}
        </InfoCard>

        <InfoCard label="Confidence">
          <span className="text-xl font-semibold text-[var(--primary)]">
            {confidence}
          </span>
        </InfoCard>
      </section>

      <section className="card rounded-xl">
        <SectionHeader title="Diagnosis Summary" />
        <div className="p-5">
          <p className="whitespace-pre-wrap text-sm leading-7 text-[var(--muted)]">
            {diagnosis.summary || "No summary available."}
          </p>
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-2">
        <AnalysisCard
          title="Triage Analysis"
          value={diagnosis.triage_reasoning}
        />

        <AnalysisCard
          title="Log Analysis"
          value={diagnosis.log_reasoning}
        />

        <section className="card rounded-xl">
          <SectionHeader title="Exception & Failure Point" />
          <div className="space-y-4 p-5">
            <Detail label="Exception Type" value={diagnosis.exception_type} />
            <Detail label="Failure Point" value={diagnosis.failure_point} />
          </div>
        </section>

        <section className="card rounded-xl">
          <SectionHeader title="Affected Code Path" />
          <div className="p-5">
            <div className="code-block">
              {diagnosis.affected_code_path || "No code path available."}
            </div>
          </div>
        </section>
      </div>

      <section className="rounded-xl border border-amber-300/50 bg-amber-50 p-4 dark:border-amber-800/50 dark:bg-amber-950/20">
        <div className="flex gap-3">
          <ShieldAlert className="mt-0.5 shrink-0 text-[var(--accent)]" size={18} />
          <div>
            <p className="text-sm font-medium">Agent output is diagnostic assistance</p>
            <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
              Review the original bug report and logs alongside the generated analysis before applying a fix.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function InfoCard({ label, children }) {
  return (
    <div className="card rounded-xl p-5">
      <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
        {label}
      </p>
      <div className="mt-3 text-sm font-medium">{children}</div>
    </div>
  );
}

function SectionHeader({ title }) {
  return (
    <div className="border-b border-[var(--border)] px-5 py-4">
      <h2 className="text-sm font-semibold">{title}</h2>
    </div>
  );
}

function AnalysisCard({ title, value }) {
  return (
    <section className="card rounded-xl">
      <SectionHeader title={title} />
      <div className="p-5">
        <p className="whitespace-pre-wrap text-sm leading-7 text-[var(--muted)]">
          {value || "No analysis available."}
        </p>
      </div>
    </section>
  );
}

function Detail({ label, value }) {
  return (
    <div>
      <p className="mb-2 text-xs font-medium text-[var(--muted)]">{label}</p>
      <div className="code-block">{value || "Not available."}</div>
    </div>
  );
}

function Message({ children }) {
  return (
    <div className="card rounded-xl p-12 text-center text-sm text-[var(--muted)]">
      {children}
    </div>
  );
}
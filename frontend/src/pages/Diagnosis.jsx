import { useEffect, useState } from "react";
import {
  ArrowLeft,
  RotateCcw,
  ShieldAlert,
  Search,
  Copy,
  Wrench,
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";
import { formatDate } from "../utils/helpers";
import { SeverityBadge } from "../components/StatusBadge";

// Parses a JSON-string field from the backend safely, returning a
// fallback (default: []) if the field is missing or not valid JSON.
function parseJsonField(value, fallback = []) {
  if (!value) return fallback;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

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

  const rootCauseEvidence = parseJsonField(diagnosis.root_cause_evidence_json);
  const duplicateMatches = parseJsonField(diagnosis.duplicate_matches_json);
  const remediationRecs = parseJsonField(diagnosis.remediation_recommendations_json);

  const hasRootCause = Boolean(diagnosis.root_cause_hypothesis);
  const hasDuplicateInfo = Boolean(diagnosis.duplicate_status);
  const hasRemediation = remediationRecs.length > 0;

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

      {/* --- Triage summary cards --- */}
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

      {/* --- Overall summary --- */}
      <section className="card rounded-xl">
        <SectionHeader title="Diagnosis Summary" />
        <div className="p-5">
          <p className="whitespace-pre-wrap text-sm leading-7 text-[var(--muted)]">
            {diagnosis.summary || "No summary available."}
          </p>
        </div>
      </section>

      {/* --- Triage + Log Analysis (Milestone 2) --- */}
      <div className="grid gap-5 xl:grid-cols-2">
        <AnalysisCard title="Triage Analysis" value={diagnosis.triage_reasoning} />
        <AnalysisCard title="Log Analysis" value={diagnosis.log_reasoning} />

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

      {/* --- Root Cause Agent (Milestone 3 / M3.1) --- */}
      <section className="card rounded-xl">
        <SectionHeader
          title="Root Cause Analysis"
          icon={<Search size={15} />}
          badge={
            hasRootCause ? (
              <ConfidenceBadge value={diagnosis.root_cause_confidence} />
            ) : (
              <InsufficientBadge />
            )
          }
        />
        <div className="space-y-5 p-5">
          {hasRootCause ? (
            <>
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--muted)]">
                  Hypothesis (agent inference)
                </p>
                <p className="text-sm leading-7">{diagnosis.root_cause_hypothesis}</p>
              </div>

              {diagnosis.root_cause_reasoning && (
                <div>
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--muted)]">
                    Reasoning
                  </p>
                  <p className="text-sm leading-7 text-[var(--muted)]">
                    {diagnosis.root_cause_reasoning}
                  </p>
                </div>
              )}

              {rootCauseEvidence.length > 0 && (
                <div>
                  <p className="mb-3 text-xs font-medium uppercase tracking-wide text-[var(--muted)]">
                    Supporting Evidence (retrieved from knowledge base)
                  </p>
                  <div className="space-y-3">
                    {rootCauseEvidence.map((ev, i) => (
                      <EvidenceRow
                        key={i}
                        bugId={ev.bug_id}
                        sourceRepo={ev.source_repo}
                        distance={ev.similarity_distance}
                        excerpt={ev.excerpt}
                      />
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <InsufficientEvidenceMessage text="Insufficient Evidence -- no similar historical defects were retrieved to ground a root cause hypothesis." />
          )}
        </div>
      </section>

      {/* --- Duplicate Detection Agent (Milestone 3 / M3.2) --- */}
      <section className="card rounded-xl">
        <SectionHeader
          title="Duplicate Detection"
          icon={<Copy size={15} />}
          badge={
            hasDuplicateInfo ? (
              <DuplicateStatusBadge status={diagnosis.duplicate_status} />
            ) : (
              <InsufficientBadge />
            )
          }
        />
        <div className="space-y-4 p-5">
          {diagnosis.duplicate_reasoning && (
            <p className="text-sm leading-7 text-[var(--muted)]">
              {diagnosis.duplicate_reasoning}
            </p>
          )}

          {duplicateMatches.length > 0 ? (
            <div className="space-y-3">
              {duplicateMatches.map((m, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-[var(--border)] p-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-semibold">Bug #{m.bug_id}</span>
                      {m.source_repo && (
                        <span className="text-[var(--muted)]">
                          ({m.source_repo})
                        </span>
                      )}
                      <MatchStatusBadge status={m.match_status} />
                    </div>
                    <span className="text-xs text-[var(--muted)]">
                      similarity {typeof m.similarity_score === "number" ? m.similarity_score.toFixed(2) : "—"}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-[var(--muted)]">{m.summary}</p>
                  {m.explanation && (
                    <p className="mt-2 text-xs italic text-[var(--muted)]">
                      {m.explanation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <InsufficientEvidenceMessage text="No matching historical bugs found -- this appears to be a new, unmatched issue." />
          )}
        </div>
      </section>

      {/* --- Remediation Agent (Milestone 3 / M3.3) --- */}
      <section className="card rounded-xl">
        <SectionHeader
          title="Recommended Fix"
          icon={<Wrench size={15} />}
          badge={
            hasRemediation ? (
              <ConfidenceBadge value={diagnosis.remediation_confidence} />
            ) : (
              <InsufficientBadge />
            )
          }
        />
        <div className="space-y-4 p-5">
          {diagnosis.remediation_reasoning && (
            <p className="text-sm leading-7 text-[var(--muted)]">
              {diagnosis.remediation_reasoning}
            </p>
          )}

          {hasRemediation ? (
            <div className="space-y-3">
              {remediationRecs.map((r, i) => (
                <div key={i} className="rounded-lg border border-[var(--border)] p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <BasisBadge basis={r.basis} />
                    <span className="text-xs text-[var(--muted)]">
                      confidence {typeof r.confidence === "number" ? `${Math.round(r.confidence * 100)}%` : "—"}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-7">{r.recommendation}</p>
                  {r.source_bug_id && (
                    <p className="mt-1 text-xs text-[var(--muted)]">
                      Based on historical bug #{r.source_bug_id}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <InsufficientEvidenceMessage text="Insufficient Evidence -- no recommendation could be generated." />
          )}
        </div>
      </section>

      <section className="rounded-xl border border-amber-300/50 bg-amber-50 p-4 dark:border-amber-800/50 dark:bg-amber-950/20">
        <div className="flex gap-3">
          <ShieldAlert className="mt-0.5 shrink-0 text-[var(--accent)]" size={18} />
          <div>
            <p className="text-sm font-medium">Agent output is diagnostic assistance</p>
            <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
              Review the original bug report and logs, and the retrieved historical
              evidence above, alongside the generated analysis before applying a fix.
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

function SectionHeader({ title, icon, badge }) {
  return (
    <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
      <h2 className="flex items-center gap-2 text-sm font-semibold">
        {icon}
        {title}
      </h2>
      {badge}
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

function InsufficientEvidenceMessage({ text }) {
  return (
    <p className="rounded-lg border border-dashed border-[var(--border)] p-4 text-sm text-[var(--muted)]">
      {text}
    </p>
  );
}

function EvidenceRow({ bugId, sourceRepo, distance, excerpt }) {
  return (
    <div className="rounded-lg border border-[var(--border)] p-3">
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold">
          Bug #{bugId} {sourceRepo ? `(${sourceRepo})` : ""}
        </span>
        <span className="text-[var(--muted)]">distance {distance}</span>
      </div>
      <p className="mt-1.5 text-xs text-[var(--muted)]">{excerpt}</p>
    </div>
  );
}

function ConfidenceBadge({ value }) {
  const pct = typeof value === "number" ? Math.round(value * 100) : null;
  const color =
    pct === null
      ? "bg-gray-100 text-gray-600"
      : pct >= 70
      ? "bg-emerald-100 text-emerald-700"
      : pct >= 45
      ? "bg-amber-100 text-amber-700"
      : "bg-rose-100 text-rose-700";

  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${color}`}>
      {pct === null ? "—" : `${pct}% confidence`}
    </span>
  );
}

function InsufficientBadge() {
  return (
    <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">
      Insufficient Evidence
    </span>
  );
}

function DuplicateStatusBadge({ status }) {
  const color =
    status === "Likely Duplicate"
      ? "bg-rose-100 text-rose-700"
      : status === "Related Issue"
      ? "bg-amber-100 text-amber-700"
      : "bg-emerald-100 text-emerald-700";

  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${color}`}>
      {status}
    </span>
  );
}

function MatchStatusBadge({ status }) {
  const color =
    status === "Likely Duplicate"
      ? "bg-rose-50 text-rose-600"
      : status === "Related Issue"
      ? "bg-amber-50 text-amber-600"
      : "bg-emerald-50 text-emerald-600";

  return (
    <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${color}`}>
      {status}
    </span>
  );
}

function BasisBadge({ basis }) {
  const labels = {
    historical_evidence: "Historical Evidence",
    root_cause_analysis: "Root Cause Analysis",
    best_practice_guideline: "Best Practice Guideline",
  };
  const colors = {
    historical_evidence: "bg-emerald-100 text-emerald-700",
    root_cause_analysis: "bg-blue-100 text-blue-700",
    best_practice_guideline: "bg-gray-100 text-gray-600",
  };

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-medium ${
        colors[basis] || "bg-gray-100 text-gray-600"
      }`}
    >
      {labels[basis] || basis}
    </span>
  );
}
import { useEffect, useState } from "react";
import { ArrowLeft, FileText, Play } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";
import { formatDate } from "../utils/helpers";
import { StatusBadge } from "../components/StatusBadge";

export default function BugDetails() {
  const { bugId } = useParams();
  const navigate = useNavigate();

  const [bug, setBug] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getBug(bugId)
      .then(setBug)
      .finally(() => setLoading(false));
  }, [bugId]);

  if (loading) {
    return <PageMessage>Loading bug details...</PageMessage>;
  }

  if (!bug) {
    return <PageMessage>Bug report could not be found.</PageMessage>;
  }

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2 text-xs font-medium text-[var(--muted)] hover:text-[var(--text)]"
      >
        <ArrowLeft size={15} />
        Back
      </button>

      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <p className="text-xs text-[var(--muted)]">BUG-{bug.id}</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            {bug.title}
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <StatusBadge status={bug.status} />
            <span className="text-xs text-[var(--muted)]">
              {bug.source_type === "file"
                ? `Uploaded: ${bug.original_filename || "file"}`
                : "Submitted by paste"}
            </span>
            <span className="text-xs text-[var(--muted)]">
              {formatDate(bug.created_at)}
            </span>
          </div>
        </div>

        <Link
          to={`/diagnosis/${bug.id}`}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white hover:opacity-90"
        >
          <Play size={15} />
          Open Diagnosis
        </Link>
      </section>

      <div className="grid gap-5 xl:grid-cols-2">
        <ContentCard title="Description">
          <p className="whitespace-pre-wrap text-sm leading-7 text-[var(--muted)]">
            {bug.description || "No description provided."}
          </p>
        </ContentCard>

        <ContentCard title="Source">
          <div className="flex items-center gap-3 rounded-lg bg-[var(--surface-2)] p-4">
            <FileText className="text-[var(--primary)]" size={20} />
            <div>
              <p className="text-sm font-medium">
                {bug.original_filename || "Pasted report"}
              </p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                Source type: {bug.source_type}
              </p>
            </div>
          </div>
        </ContentCard>

        <ContentCard title="Stack Trace">
          <CodeBlock value={bug.stack_trace} />
        </ContentCard>

        <ContentCard title="Error Log">
          <CodeBlock value={bug.error_log} />
        </ContentCard>
      </div>
    </div>
  );
}

function ContentCard({ title, children }) {
  return (
    <section className="card rounded-xl p-5">
      <h2 className="mb-4 text-sm font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function CodeBlock({ value }) {
  return (
    <div className="code-block min-h-28">
      {value || "No data provided."}
    </div>
  );
}

function PageMessage({ children }) {
  return (
    <div className="card rounded-xl p-12 text-center text-sm text-[var(--muted)]">
      {children}
    </div>
  );
}
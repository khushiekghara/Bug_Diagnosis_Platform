import { useRef, useState } from "react";
import { FileUp, ClipboardPaste, UploadCloud } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

const initialPaste = {
  title: "",
  description: "",
  stack_trace: "",
  error_log: "",
};

export default function SubmitBug({ onSubmitted }) {
  const navigate = useNavigate();
  const fileRef = useRef(null);

  const [mode, setMode] = useState("paste");
  const [paste, setPaste] = useState(initialPaste);
  const [fileTitle, setFileTitle] = useState("");
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handlePasteChange = (event) => {
    setPaste((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const chooseFile = (selectedFile) => {
    if (!selectedFile) return;

    const allowed = [".txt", ".log", ".json", ".csv"];
    const extension = selectedFile.name.includes(".")
      ? `.${selectedFile.name.split(".").pop().toLowerCase()}`
      : "";

    if (!allowed.includes(extension)) {
      setError("Only .txt, .log, .json and .csv files are allowed.");
      return;
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      setError("The maximum file size is 5 MB.");
      return;
    }

    setError("");
    setFile(selectedFile);
  };

  const submitPaste = async (event) => {
    event.preventDefault();
    setError("");

    if (paste.title.trim().length < 3) {
      setError("Bug title must contain at least 3 characters.");
      return;
    }

    if (
      !paste.description.trim() &&
      !paste.stack_trace.trim() &&
      !paste.error_log.trim()
    ) {
      setError("Provide a description, stack trace, or error log.");
      return;
    }

    try {
      setSubmitting(true);

      const bug = await api.submitPaste({
        title: paste.title.trim(),
        description: paste.description.trim() || null,
        stack_trace: paste.stack_trace.trim() || null,
        error_log: paste.error_log.trim() || null,
      });

      onSubmitted?.();
      navigate(`/diagnosis/${bug.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const submitFile = async (event) => {
    event.preventDefault();
    setError("");

    if (fileTitle.trim().length < 3) {
      setError("Bug title must contain at least 3 characters.");
      return;
    }

    if (!file) {
      setError("Please choose a bug log file.");
      return;
    }

    try {
      setSubmitting(true);

      const bug = await api.uploadBug(fileTitle.trim(), file);

      onSubmitted?.();
      navigate(`/diagnosis/${bug.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <section>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--primary)]">
          New report
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
          Submit a Bug
        </h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Submit a description or upload a log. Your backend will run the agent pipeline automatically.
        </p>
      </section>

      {error && (
        <div className="rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="card rounded-xl">
        <div className="flex border-b border-[var(--border)]">
          <button
            onClick={() => setMode("paste")}
            className={`flex flex-1 items-center justify-center gap-2 px-4 py-3 text-sm font-medium ${
              mode === "paste"
                ? "border-b-2 border-[var(--primary)] text-[var(--primary)]"
                : "text-[var(--muted)]"
            }`}
          >
            <ClipboardPaste size={16} />
            Paste report
          </button>

          <button
            onClick={() => setMode("upload")}
            className={`flex flex-1 items-center justify-center gap-2 px-4 py-3 text-sm font-medium ${
              mode === "upload"
                ? "border-b-2 border-[var(--primary)] text-[var(--primary)]"
                : "text-[var(--muted)]"
            }`}
          >
            <FileUp size={16} />
            Upload log
          </button>
        </div>

        {mode === "paste" ? (
          <form onSubmit={submitPaste} className="space-y-5 p-5 sm:p-7">
            <Field
              label="Bug title"
              name="title"
              value={paste.title}
              onChange={handlePasteChange}
              placeholder="Example: Login API returns HTTP 500"
              required
            />

            <Field
              label="Description"
              name="description"
              value={paste.description}
              onChange={handlePasteChange}
              placeholder="Describe what happened, expected behavior, and actual behavior."
              textarea
            />

            <Field
              label="Stack trace"
              name="stack_trace"
              value={paste.stack_trace}
              onChange={handlePasteChange}
              placeholder="Paste the stack trace here..."
              textarea
              mono
            />

            <Field
              label="Error log"
              name="error_log"
              value={paste.error_log}
              onChange={handlePasteChange}
              placeholder="Paste relevant application logs here..."
              textarea
              mono
            />

            <SubmitButton loading={submitting}>
              {submitting ? "Running diagnosis..." : "Analyze Bug"}
            </SubmitButton>
          </form>
        ) : (
          <form onSubmit={submitFile} className="space-y-5 p-5 sm:p-7">
            <Field
              label="Bug title"
              value={fileTitle}
              onChange={(event) => setFileTitle(event.target.value)}
              placeholder="Example: Database connection failure"
              required
            />

            <div>
              <label className="mb-2 block text-xs font-medium text-[var(--muted)]">
                Bug log file
              </label>

              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(event) => {
                  event.preventDefault();
                  setDragging(false);
                  chooseFile(event.dataTransfer.files?.[0]);
                }}
                className={`w-full rounded-xl border border-dashed p-10 text-center transition ${
                  dragging
                    ? "border-[var(--primary)] bg-[var(--primary-soft)]"
                    : "border-[var(--border)] bg-[var(--surface-2)] hover:border-[var(--primary)]"
                }`}
              >
                <UploadCloud
                  className="mx-auto mb-3 text-[var(--primary)]"
                  size={30}
                />
                <p className="text-sm font-medium">
                  {file ? file.name : "Choose a file or drag it here"}
                </p>
                <p className="mt-2 text-xs text-[var(--muted)]">
                  .txt, .log, .json or .csv · maximum 5 MB
                </p>
              </button>

              <input
                ref={fileRef}
                type="file"
                accept=".txt,.log,.json,.csv"
                className="hidden"
                onChange={(event) => chooseFile(event.target.files?.[0])}
              />
            </div>

            <SubmitButton loading={submitting}>
              {submitting ? "Running diagnosis..." : "Upload & Analyze"}
            </SubmitButton>
          </form>
        )}
      </div>
    </div>
  );
}

function Field({
  label,
  name,
  value,
  onChange,
  placeholder,
  textarea = false,
  mono = false,
  required = false,
}) {
  const className = [
    "w-full rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2.5 text-sm outline-none transition",
    "placeholder:text-[var(--muted)] focus:border-[var(--primary)]",
    mono ? "font-mono text-xs leading-6" : "",
  ].join(" ");

  return (
    <div>
      <label className="mb-2 block text-xs font-medium text-[var(--muted)]">
        {label} {required && <span className="text-[var(--danger)]">*</span>}
      </label>

      {textarea ? (
        <textarea
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={className}
        />
      ) : (
        <input
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={className}
          required={required}
        />
      )}
    </div>
  );
}

function SubmitButton({ children, loading }) {
  return (
    <button
      disabled={loading}
      className="w-full rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {children}
    </button>
  );
}
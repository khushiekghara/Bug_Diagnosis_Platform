export function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function getSeverityClass(severity = "") {
  const value = severity.toLowerCase();

  if (value.includes("critical") || value.includes("high")) {
    return "bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-300";
  }

  if (value.includes("medium")) {
    return "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300";
  }

  if (value.includes("low")) {
    return "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300";
  }

  return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300";
}

export function getStatusClass(status = "") {
  return status.toLowerCase() === "analyzed"
    ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
    : "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300";
}
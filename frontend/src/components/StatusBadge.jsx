import { getSeverityClass, getStatusClass } from "../utils/helpers";

export function StatusBadge({ status }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-medium ${getStatusClass(status)}`}>
      {status || "unknown"}
    </span>
  );
}

export function SeverityBadge({ severity }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-medium ${getSeverityClass(severity)}`}>
      {severity || "Not available"}
    </span>
  );
}
import { Menu, Moon, Sun } from "lucide-react";
import { useTheme } from "../context/ThemeContext";

export default function Topbar({ onMenuClick, apiOnline }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-30 border-b border-[var(--border)] bg-[var(--bg)]/90 backdrop-blur">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuClick}
            className="rounded-lg p-2 text-[var(--muted)] hover:bg-[var(--surface-2)] lg:hidden"
          >
            <Menu size={19} />
          </button>

          <div>
            <p className="text-sm font-semibold">Bug Diagnosis Platform</p>
            <p className="hidden text-[11px] text-[var(--muted)] sm:block">
              AI-assisted software bug analysis
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-2 rounded-full border border-[var(--border)] px-3 py-1.5 text-xs sm:flex">
            <span
              className={`h-2 w-2 rounded-full ${
                apiOnline ? "bg-emerald-500" : "bg-red-500"
              }`}
            />
            <span className="text-[var(--muted)]">
              {apiOnline ? "Backend online" : "Backend offline"}
            </span>
          </div>

          <button
            onClick={toggleTheme}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            className="rounded-lg border border-[var(--border)] p-2 text-[var(--muted)] transition hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
          >
            {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
          </button>
        </div>
      </div>
    </header>
  );
}
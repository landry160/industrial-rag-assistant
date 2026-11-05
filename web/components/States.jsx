import { RefreshCw, TriangleAlert } from "lucide-react";

export function ErrorCard({ message, onRetry }) {
  return (
    <div className="glass-panel animate-slide-up flex flex-col items-start gap-4 rounded-[32px] p-6 sm:flex-row sm:items-center">
      <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-red-200 bg-red-100 text-red-600 shadow-inner dark:border-red-400/20 dark:bg-red-500/15 dark:text-red-300">
        <TriangleAlert className="h-6 w-6" aria-hidden />
      </span>
      <p className="flex-1 text-sm font-bold">{message}</p>
      <button type="button" className="btn-glass" onClick={onRetry}>
        <RefreshCw className="h-4 w-4" aria-hidden />
        Réessayer
      </button>
    </div>
  );
}

export function EmptyIcon({ icon: Icon }) {
  return (
    <span
      className="flex h-20 w-20 items-center justify-center rounded-[28px] border border-white/60 shadow-inner dark:border-white/10"
      style={{ background: "var(--primary-soft)", color: "var(--on-soft)" }}
    >
      <Icon className="h-9 w-9" aria-hidden />
    </span>
  );
}

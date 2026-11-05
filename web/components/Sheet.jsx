"use client";

import { useEffect } from "react";
import { X } from "lucide-react";

/** Modale glass sur grand écran, bottom sheet sur téléphone. */
export default function Sheet({ open, onClose, title, children }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center md:items-center md:p-6">
      <button
        type="button"
        aria-label="Fermer"
        tabIndex={-1}
        onClick={onClose}
        className="absolute inset-0 cursor-default bg-slate-900/40 backdrop-blur-sm"
      />
      <section
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="glass-panel animate-sheet-up md:animate-pop-in relative max-h-[85dvh] w-full overflow-y-auto rounded-t-[32px] p-6 md:max-w-lg md:rounded-[32px] md:p-8"
        style={{ background: "var(--glass-panel)", paddingBottom: "max(1.5rem, env(safe-area-inset-bottom))" }}
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <h2 className="min-w-0 break-words text-2xl font-black tracking-tight">{title}</h2>
          <button type="button" className="btn-glass w-11 shrink-0 !px-0" aria-label="Fermer" onClick={onClose} autoFocus>
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}

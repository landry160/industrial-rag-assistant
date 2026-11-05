"use client";

import { useEffect, useState } from "react";
import { Check, Monitor, Moon, Sun } from "lucide-react";
import Sheet from "@/components/Sheet";
import { DEFAULT_THEME, PRESETS, applyTheme, readTheme, saveTheme } from "@/lib/theme";

const MODES = [
  { id: "light", label: "Clair", icon: Sun },
  { id: "dark", label: "Sombre", icon: Moon },
  { id: "system", label: "Système", icon: Monitor },
];

export default function AppearancePanel({ open, onClose }) {
  const [theme, setTheme] = useState(DEFAULT_THEME);

  useEffect(() => {
    const saved = readTheme();
    setTheme(saved);
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      const current = readTheme();
      if (current.mode === "system") applyTheme(current);
    };
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  function update(change) {
    const next = { ...theme, ...change };
    setTheme(next);
    saveTheme(next);
  }

  return (
    <Sheet open={open} onClose={onClose} title="Apparence">
      <p className="label-meta mb-2">Mode d'affichage</p>
      <div className="mb-6 grid grid-cols-3 gap-2">
        {MODES.map(({ id, label, icon: Icon }) => {
          const active = theme.mode === id;
          return (
            <button
              key={id}
              type="button"
              aria-pressed={active}
              onClick={() => update({ mode: id })}
              className="btn-glass !min-h-[64px] flex-col !gap-1"
              style={active ? { borderColor: "var(--primary)", background: "var(--primary-soft)" } : undefined}
            >
              <Icon className="h-5 w-5" aria-hidden />
              {label}
            </button>
          );
        })}
      </div>

      <p className="label-meta mb-2">Thème de couleur</p>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {PRESETS.map(({ id, label, swatch }) => {
          const active = theme.preset === id;
          return (
            <button
              key={id}
              type="button"
              aria-pressed={active}
              onClick={() => update({ preset: id })}
              className="btn-glass !justify-start"
              style={active ? { borderColor: "var(--primary)", background: "var(--primary-soft)" } : undefined}
            >
              <span className="h-6 w-6 rounded-lg" style={{ background: swatch }} aria-hidden />
              {label}
              {active && <Check className="ml-auto h-4 w-4" aria-hidden />}
            </button>
          );
        })}
      </div>
    </Sheet>
  );
}

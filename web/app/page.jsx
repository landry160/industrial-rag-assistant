"use client";

import { useCallback, useEffect, useState } from "react";
import { BookOpen, MessageCircleQuestion, Palette } from "lucide-react";
import AppearancePanel from "@/components/AppearancePanel";
import AskView from "@/components/AskView";
import DocumentsView from "@/components/DocumentsView";
import Scene from "@/components/Scene";
import { ToastProvider } from "@/components/Toasts";
import { getConfig, getDocuments } from "@/lib/api";

const NAV = [
  { id: "ask", label: "Assistant", icon: MessageCircleQuestion },
  { id: "documents", label: "Documents", icon: BookOpen },
];

export default function Home() {
  const [view, setView] = useState("ask");
  const [appearanceOpen, setAppearanceOpen] = useState(false);
  const [settings, setSettings] = useState(null);
  const [documents, setDocuments] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [thread, setThread] = useState([]);

  const refresh = useCallback(async () => {
    setLoadError(null);
    try {
      const [config, docs] = await Promise.all([getConfig(), getDocuments()]);
      setSettings(config);
      setDocuments(docs);
    } catch (error) {
      setDocuments(null);
      setLoadError(error.message);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const shared = { settings, documents, loadError, refresh };

  return (
    <ToastProvider>
      <Scene />

      <header className="glass-nav fixed inset-x-0 top-0 z-30 border-b">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4 md:px-6">
          <button
            type="button"
            onClick={() => setView("ask")}
            className="btn-press flex min-h-[44px] items-center gap-3 rounded-2xl text-left"
          >
            <span
              className="flex h-10 w-10 items-center justify-center rounded-2xl text-white"
              style={{ background: "var(--gradient-primary)", boxShadow: "var(--shadow-primary)" }}
            >
              <BookOpen className="h-5 w-5" aria-hidden />
            </span>
            <span className="text-base font-black tracking-tight">Assistant RAG</span>
          </button>

          <nav className="hidden items-center gap-2 md:flex" aria-label="Navigation principale">
            {NAV.map((item) => (
              <NavButton key={item.id} item={item} active={view === item.id} onClick={() => setView(item.id)} />
            ))}
          </nav>

          <button
            type="button"
            className="btn-glass w-11 !px-0"
            aria-label="Ouvrir les réglages d'apparence"
            onClick={() => setAppearanceOpen(true)}
          >
            <Palette className="h-5 w-5" aria-hidden />
          </button>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 pt-24 md:px-6">
        {/* Les deux vues restent montées : changer d'onglet ne perd ni la conversation ni un envoi en cours. */}
        <div hidden={view !== "ask"}>
          <AskView {...shared} thread={thread} setThread={setThread} onOpenDocuments={() => setView("documents")} />
        </div>
        <div hidden={view !== "documents"}>
          <DocumentsView {...shared} />
        </div>
      </main>

      <nav
        className="glass-nav fixed inset-x-0 bottom-0 z-30 grid grid-cols-2 border-t px-2 pt-2 md:hidden"
        style={{ paddingBottom: "max(0.5rem, env(safe-area-inset-bottom))" }}
        aria-label="Navigation principale"
      >
        {NAV.map((item) => (
          <NavButton key={item.id} item={item} active={view === item.id} onClick={() => setView(item.id)} stacked />
        ))}
      </nav>

      <AppearancePanel open={appearanceOpen} onClose={() => setAppearanceOpen(false)} />
    </ToastProvider>
  );
}

function NavButton({ item, active, onClick, stacked = false }) {
  const Icon = item.icon;
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      className={`btn-press flex min-h-[48px] items-center justify-center rounded-2xl px-4 font-bold ${
        stacked ? "flex-col gap-0.5 text-[11px]" : "gap-2 text-sm"
      }`}
      style={active ? { background: "var(--primary-soft)", color: "var(--on-soft)" } : { color: "var(--ink-soft)" }}
    >
      <Icon className="h-5 w-5" aria-hidden />
      <span>{item.label}</span>
    </button>
  );
}

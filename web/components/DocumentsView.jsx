"use client";

import { useRef, useState } from "react";
import { FileText, FileType, FileUp, Layers, LockKeyhole, RefreshCw, Sparkles, Trash2, UploadCloud } from "lucide-react";
import Sheet from "@/components/Sheet";
import { EmptyIcon, ErrorCard } from "@/components/States";
import { useToast } from "@/components/Toasts";
import { deleteDocument, loadSample, uploadDocument } from "@/lib/api";

const ENGINE = {
  gemini: "Gemini",
  anthropic: "Claude",
  extractive: "Extraits",
};

const TILE_BY_TYPE = { pdf: "tile-accent", txt: "tile-primary", md: "tile-success" };

const extensionOf = (name) => name.split(".").pop().toLowerCase();

const formatDate = (iso) =>
  new Date(iso).toLocaleDateString("fr-CA", { day: "numeric", month: "long", year: "numeric" });

export default function DocumentsView({ settings, documents, loadError, refresh }) {
  const [uploading, setUploading] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [toDelete, setToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [token, setToken] = useState("");
  const [tokenError, setTokenError] = useState(false);
  const inputRef = useRef(null);
  const toast = useToast();

  const locked = Boolean(settings?.writes_protected);
  const blocked = locked && !token.trim();
  const totalChunks = (documents ?? []).reduce((sum, doc) => sum + doc.chunks, 0);

  function handleWriteError(error) {
    if (error.status === 401) setTokenError(true);
    toast(error.message, "error");
  }

  async function onFiles(fileList) {
    const files = [...fileList];
    if (!files.length || uploading || blocked) return;
    let added = 0;
    for (const file of files) {
      setUploading(file.name);
      try {
        const result = await uploadDocument(file, token.trim());
        added += 1;
        toast(
          result.status === "unchanged"
            ? `« ${result.source} » est déjà à jour`
            : `« ${result.source} » ajouté : ${result.chunks_indexed} passage${result.chunks_indexed > 1 ? "s" : ""}`,
          result.status === "unchanged" ? "info" : "success",
        );
      } catch (error) {
        handleWriteError(error);
      }
    }
    setUploading(null);
    if (inputRef.current) inputRef.current.value = "";
    if (added) await refresh();
  }

  async function onDelete() {
    setDeleting(true);
    try {
      await deleteDocument(toDelete.id, token.trim());
      toast(`« ${toDelete.source} » supprimé`);
      setToDelete(null);
      await refresh();
    } catch (error) {
      setToDelete(null);
      handleWriteError(error);
    } finally {
      setDeleting(false);
    }
  }

  async function onSample() {
    try {
      const { documents: count } = await loadSample(token.trim());
      toast(`${count} documents d'exemple chargés`);
      await refresh();
    } catch (error) {
      handleWriteError(error);
    }
  }

  return (
    <section className="pb-32 md:pb-12">
      <h1 className="text-4xl font-black tracking-tighter drop-shadow-sm md:text-5xl">Documents</h1>
      <p className="mt-2 text-sm font-medium" style={{ color: "var(--ink-soft)" }}>
        L'assistant répond uniquement à partir de ce que vous ajoutez ici.
      </p>

      {loadError ? (
        <div className="mt-6">
          <ErrorCard message={loadError} onRetry={refresh} />
        </div>
      ) : (
        <>
          <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-3">
            <Stat label="Documents" value={documents?.length} icon={FileText} tone="tile-primary" />
            <Stat label="Passages indexés" value={documents ? totalChunks : undefined} icon={Layers} tone="tile-accent" />
            <Stat label="Moteur de réponse" value={settings ? ENGINE[settings.provider] : undefined} icon={Sparkles} tone="tile-success" />
          </div>

          {settings?.provider === "extractive" && (
            <p className="glass-card mt-5 rounded-2xl p-4 text-sm font-bold">
              Aucune clé d'IA n'est configurée : l'assistant affiche les passages d'origine sans les reformuler.
            </p>
          )}

          {locked && (
            <div className="glass-card mt-5 rounded-[28px] p-5">
              <label htmlFor="token" className="label-meta mb-2 flex items-center gap-1.5">
                <LockKeyhole className="h-3.5 w-3.5" aria-hidden />
                Code d'accès pour modifier les documents
              </label>
              <input
                id="token"
                type="password"
                autoComplete="off"
                value={token}
                aria-invalid={tokenError}
                onChange={(event) => {
                  setToken(event.target.value);
                  setTokenError(false);
                }}
                className="glass-input min-h-[48px] w-full rounded-2xl px-4 text-sm font-bold sm:max-w-sm"
              />
              {tokenError && (
                <p className="mt-2 text-sm font-bold text-red-600 dark:text-red-300">Ce code d'accès n'est pas valide.</p>
              )}
            </div>
          )}

          <div
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragging(false);
              onFiles(event.dataTransfer.files);
            }}
            className="glass-panel mt-5 flex flex-col items-center gap-3 rounded-[32px] border-2 border-dashed p-6 text-center transition-colors duration-200 md:p-8"
            style={dragging ? { borderColor: "var(--primary)", background: "var(--primary-soft)" } : undefined}
          >
            {uploading ? (
              <div className="w-full max-w-md">
                <p className="mb-3 truncate text-sm font-black">{uploading}</p>
                <div className="progress-bar" />
                <p className="label-meta mt-3">Lecture et indexation en cours…</p>
              </div>
            ) : (
              <>
                <UploadCloud className="h-8 w-8" style={{ color: "var(--primary)" }} aria-hidden />
                <p className="text-sm font-bold">
                  <span className="hidden md:inline">Glissez vos fichiers ici, ou choisissez-les. </span>
                  PDF, TXT ou MD, jusqu'à {settings?.max_upload_mb ?? 25} Mo.
                </p>
                <input
                  ref={inputRef}
                  type="file"
                  multiple
                  accept={settings?.extensions?.join(",") ?? ".pdf,.txt,.md"}
                  className="sr-only"
                  aria-label="Choisir des fichiers à ajouter"
                  onChange={(event) => onFiles(event.target.files)}
                />
                <button type="button" className="btn-primary" disabled={blocked} onClick={() => inputRef.current?.click()}>
                  <FileUp className="h-5 w-5" aria-hidden />
                  Ajouter un document
                </button>
              </>
            )}
          </div>

          <div className="mt-8">
            {documents === null ? (
              <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3" aria-label="Chargement">
                {[0, 1, 2].map((key) => (
                  <div key={key} className="skeleton h-44 !rounded-[28px]" />
                ))}
              </div>
            ) : documents.length === 0 ? (
              <div className="glass-card flex flex-col items-center gap-3 rounded-[32px] p-8 text-center">
                <EmptyIcon icon={FileType} />
                <p className="text-lg font-black tracking-tight">Aucun document pour l'instant</p>
                <p className="text-sm font-medium" style={{ color: "var(--ink-soft)" }}>
                  Ajoutez votre premier manuel, ou essayez avec trois fiches d'exemple.
                </p>
                <button type="button" className="btn-glass" disabled={blocked} onClick={onSample}>
                  <Sparkles className="h-4 w-4" aria-hidden />
                  Charger les exemples
                </button>
              </div>
            ) : (
              <ul className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                {documents.map((doc) => (
                  <DocumentTile key={doc.id} doc={doc} disabled={blocked} onDelete={() => setToDelete(doc)} />
                ))}
              </ul>
            )}
          </div>
        </>
      )}

      <Sheet open={Boolean(toDelete)} onClose={() => setToDelete(null)} title="Supprimer ce document ?">
        {toDelete && (
          <>
            <p className="break-words text-sm font-medium">
              <strong className="font-black">{toDelete.source}</strong> et ses passages seront retirés. L'assistant ne pourra plus s'en servir.
            </p>
            <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button type="button" className="btn-glass" onClick={() => setToDelete(null)}>
                Annuler
              </button>
              <button
                type="button"
                disabled={deleting}
                onClick={onDelete}
                className="btn-press inline-flex min-h-[44px] items-center justify-center gap-2 rounded-2xl px-5 text-sm font-black text-white disabled:opacity-50"
                style={{ background: "linear-gradient(135deg, #e11d48 0%, #be123c 100%)", boxShadow: "0 15px 35px rgba(255,43,94,0.3)" }}
              >
                <Trash2 className="h-4 w-4" aria-hidden />
                Supprimer le document
              </button>
            </div>
          </>
        )}
      </Sheet>
    </section>
  );
}

function Stat({ label, value, icon: Icon, tone }) {
  return (
    <div className={`tile tile-pattern ${tone} p-5`}>
      <div className="relative z-10 flex items-center justify-between">
        <p className="text-[11px] font-black uppercase tracking-widest opacity-90">{label}</p>
        <Icon className="h-5 w-5" aria-hidden />
      </div>
      {value === undefined ? (
        <div className="relative z-10 mt-3 h-9 w-20 rounded-xl bg-white/20" />
      ) : (
        <p className="relative z-10 mt-2 text-4xl font-black tabular-nums tracking-tighter">{value}</p>
      )}
    </div>
  );
}

function DocumentTile({ doc, disabled, onDelete }) {
  const type = extensionOf(doc.source);
  return (
    <li className={`tile tile-pattern ${TILE_BY_TYPE[type] ?? "tile-primary"} flex min-h-44 flex-col p-5 hover:-translate-y-1`}>
      <div className="relative z-10 flex items-center justify-between gap-2">
        <span className="glass-badge">{type}</span>
        <button
          type="button"
          aria-label={`Supprimer ${doc.source}`}
          disabled={disabled}
          onClick={onDelete}
          className="btn-press flex h-11 w-11 items-center justify-center rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md hover:bg-white/20 disabled:opacity-50"
        >
          <Trash2 className="h-4 w-4" aria-hidden />
        </button>
      </div>
      <p className="relative z-10 mt-3 line-clamp-2 break-words text-lg font-black leading-tight tracking-tight">{doc.source}</p>
      <div className="relative z-10 mt-auto pt-3 text-xs font-bold opacity-95">
        <p className="tabular-nums">
          {doc.chunks} passage{doc.chunks > 1 ? "s" : ""}
          {doc.pages ? ` · ${doc.pages} page${doc.pages > 1 ? "s" : ""}` : ""}
        </p>
        <p>Ajouté le {formatDate(doc.created_at)}</p>
        {doc.needs_reindex && (
          <p className="mt-2 flex items-center gap-1.5 font-black">
            <RefreshCw className="h-3.5 w-3.5" aria-hidden />
            À ajouter de nouveau : le modèle a changé
          </p>
        )}
      </div>
    </li>
  );
}

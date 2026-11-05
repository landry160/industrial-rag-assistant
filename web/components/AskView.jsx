"use client";

import { useRef, useState } from "react";
import { ArrowUp, BookOpen, FileSearch, FileUp, Loader2, SearchX, Sparkles, TriangleAlert } from "lucide-react";
import Sheet from "@/components/Sheet";
import { EmptyIcon, ErrorCard } from "@/components/States";
import { useToast } from "@/components/Toasts";
import { askQuestion, loadSample } from "@/lib/api";

const SUGGESTIONS = [
  "À quelle fréquence inspecter la courroie du convoyeur C-12 ?",
  "Que faire en cas de fuite sur la presse H-40 ?",
  "Quelle est la référence de la sonde du capteur T-88 ?",
];
const SAMPLE_SOURCE = "maintenance-convoyeur-C12.txt";

const pageLabel = (source) => (source.page ? `p. ${source.page}` : null);

export default function AskView({ settings, documents, loadError, refresh, thread, setThread, onOpenDocuments }) {
  const [question, setQuestion] = useState("");
  const [loadingSample, setLoadingSample] = useState(false);
  const [openSource, setOpenSource] = useState(null);
  const endRef = useRef(null);
  const toast = useToast();

  const busy = thread.some((item) => item.status === "loading");
  const canAsk = question.trim().length >= 3 && !busy;

  async function run(id, text) {
    setThread((items) =>
      items.map((item) => (item.id === id ? { ...item, status: "loading", error: null } : item)),
    );
    try {
      const result = await askQuestion(text);
      setThread((items) => items.map((item) => (item.id === id ? { ...item, status: "done", result } : item)));
    } catch (error) {
      setThread((items) =>
        items.map((item) => (item.id === id ? { ...item, status: "error", error: error.message } : item)),
      );
    }
  }

  function submit(text) {
    const trimmed = text.trim();
    if (trimmed.length < 3 || busy) return;
    const id = Date.now();
    setThread((items) => [...items, { id, question: trimmed, status: "loading" }]);
    setQuestion("");
    run(id, trimmed);
    setTimeout(() => endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }), 50);
  }

  async function onLoadSample() {
    setLoadingSample(true);
    try {
      const { documents: count } = await loadSample();
      toast(`${count} documents d'exemple chargés`);
      await refresh();
    } catch (error) {
      if (error.status === 401) {
        toast("Ajoutez votre code d'accès dans Documents.", "info");
        onOpenDocuments();
      } else {
        toast(error.message, "error");
      }
    } finally {
      setLoadingSample(false);
    }
  }

  if (loadError) {
    return (
      <section className="mx-auto max-w-2xl pt-10">
        <ErrorCard message={loadError} onRetry={refresh} />
      </section>
    );
  }

  if (documents === null) return <AskSkeleton />;

  if (documents.length === 0) {
    return (
      <section className="mx-auto flex max-w-2xl animate-slide-up flex-col items-center pb-32 pt-8 text-center md:pt-16">
        <EmptyIcon icon={FileSearch} />
        <h1 className="mt-6 text-4xl font-black tracking-tighter drop-shadow-sm md:text-6xl">
          Vos manuels ont les réponses.
        </h1>
        <p className="mt-4 max-w-lg text-base font-medium" style={{ color: "var(--ink-soft)" }}>
          Ajoutez un premier document, ou essayez avec trois fiches d'exemple. Chaque réponse citera sa source.
        </p>
        <div className="mt-8 flex w-full flex-col items-center gap-3 sm:w-auto sm:flex-row">
          <button type="button" className="btn-primary w-full sm:w-auto" onClick={onLoadSample} disabled={loadingSample}>
            {loadingSample ? <Loader2 className="h-5 w-5 animate-spin" aria-hidden /> : <Sparkles className="h-5 w-5" aria-hidden />}
            Essayer avec les exemples
          </button>
          <button type="button" className="btn-glass w-full !rounded-full !px-6 sm:w-auto" onClick={onOpenDocuments}>
            <FileUp className="h-4 w-4" aria-hidden />
            Ajouter mon document
          </button>
        </div>
      </section>
    );
  }

  const hasThread = thread.length > 0;
  const hasSample = documents.some((doc) => doc.source === SAMPLE_SOURCE);

  const composer = (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        submit(question);
      }}
      className="glass-panel flex items-center gap-2 rounded-full p-2 shadow-[0_15px_40px_rgba(0,0,0,0.1)]"
    >
      <label htmlFor="question" className="sr-only">
        Votre question technique
      </label>
      <input
        id="question"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        maxLength={1000}
        autoComplete="off"
        enterKeyHint="send"
        placeholder="Posez votre question…"
        className="min-h-[52px] min-w-0 flex-1 rounded-full bg-transparent px-5 text-base font-bold outline-none placeholder:font-medium placeholder:text-slate-500 dark:placeholder:text-slate-300"
      />
      <button type="submit" className="btn-primary shrink-0 !px-4 sm:!px-7" disabled={!canAsk} aria-label="Poser la question">
        {busy ? <Loader2 className="h-5 w-5 animate-spin" aria-hidden /> : <ArrowUp className="h-5 w-5" aria-hidden />}
        <span className="hidden sm:inline">Poser la question</span>
      </button>
    </form>
  );

  return (
    <section className={hasThread ? "mx-auto max-w-3xl pb-48 md:pb-36" : "mx-auto max-w-3xl pb-32"}>
      {!hasThread && (
        <div className="animate-slide-up pt-6 text-center md:pt-14">
          <h1 className="text-4xl font-black tracking-tighter drop-shadow-sm md:text-6xl">
            Quelle est votre question technique ?
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base font-medium" style={{ color: "var(--ink-soft)" }}>
            La réponse vient uniquement de vos {documents.length} document{documents.length > 1 ? "s" : ""}, avec la source à l'appui.
          </p>
          <div className="mt-8 text-left">{composer}</div>
          {hasSample && (
            <div className="mt-6 flex flex-col gap-2">
              <p className="label-meta text-left">Pour commencer</p>
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="btn-glass !justify-start !rounded-2xl !py-2 text-left"
                  onClick={() => submit(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="flex flex-col gap-6" aria-live="polite">
        {thread.map((item) => (
          <article key={item.id} className="animate-slide-up flex flex-col gap-3">
            <p
              className="ml-auto max-w-[85%] rounded-[24px] rounded-br-lg px-5 py-3 text-sm font-bold text-white"
              style={{ background: "var(--gradient-tile)", boxShadow: "var(--shadow-primary)" }}
            >
              {item.question}
            </p>
            {item.status === "loading" && <AnswerLoading />}
            {item.status === "error" && <ErrorCard message={item.error} onRetry={() => run(item.id, item.question)} />}
            {item.status === "done" && <Answer result={item.result} onOpenSource={setOpenSource} onOpenDocuments={onOpenDocuments} />}
          </article>
        ))}
      </div>
      <div ref={endRef} />

      {hasThread && (
        <div
          className="fixed inset-x-0 z-20 px-4 md:bottom-6 md:px-6"
          style={{ bottom: "calc(76px + env(safe-area-inset-bottom))" }}
        >
          <div className="mx-auto max-w-3xl">{composer}</div>
        </div>
      )}

      <Sheet open={Boolean(openSource)} onClose={() => setOpenSource(null)} title={openSource?.document ?? ""}>
        {openSource && (
          <>
            <div className="mb-4 flex flex-wrap gap-2">
              {pageLabel(openSource) && <span className="label-meta">{pageLabel(openSource)}</span>}
              <span className="label-meta tabular-nums">Pertinence {Math.round(openSource.score * 100)} %</span>
            </div>
            <p className="whitespace-pre-line text-sm font-medium leading-relaxed">{openSource.section}</p>
          </>
        )}
      </Sheet>
    </section>
  );
}

function Answer({ result, onOpenSource, onOpenDocuments }) {
  if (!result.grounded) {
    return (
      <div className="glass-panel flex flex-col items-start gap-4 rounded-[32px] p-6 sm:flex-row sm:items-center">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-amber-200 bg-amber-100 text-amber-700 shadow-inner dark:border-amber-400/20 dark:bg-amber-500/15 dark:text-amber-300">
          <SearchX className="h-6 w-6" aria-hidden />
        </span>
        <p className="flex-1 text-sm font-bold">{result.answer}</p>
        <button type="button" className="btn-glass" onClick={onOpenDocuments}>
          <FileUp className="h-4 w-4" aria-hidden />
          Ajouter un document
        </button>
      </div>
    );
  }

  const byId = Object.fromEntries(result.sources.map((source) => [source.id, source]));

  return (
    <div className="glass-panel rounded-[32px] p-6 md:p-8">
      {result.notice && (
        <p className="mb-4 flex items-start gap-2 rounded-2xl border border-amber-300/60 bg-amber-100/70 p-3 text-sm font-bold text-amber-900 dark:bg-amber-500/15 dark:text-amber-100">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          {result.notice}
        </p>
      )}
      {result.mode === "extractive" && !result.notice && (
        <p className="label-meta mb-3">Passages d'origine, sans reformulation</p>
      )}
      <AnswerText text={result.answer} sources={byId} onOpenSource={onOpenSource} />

      <p className="label-meta mb-3 mt-6">Sources</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {result.sources.map((source) => (
          <SourceTile key={source.id} source={source} onOpen={() => onOpenSource(source)} />
        ))}
      </div>
    </div>
  );
}

function SourceTile({ source, onOpen }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="tile tile-pattern tile-primary btn-press flex flex-col p-4 text-left hover:-translate-y-1"
    >
      <span className="relative z-10 flex items-center justify-between gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-white/20 text-xs font-black tabular-nums">
          {source.id}
        </span>
        <span className="glass-badge tabular-nums">{Math.round(source.score * 100)} %</span>
      </span>
      <span className="relative z-10 mt-3 block break-words text-sm font-black leading-snug">{source.document}</span>
      {source.page && <span className="relative z-10 text-xs font-bold opacity-90">Page {source.page}</span>}
      <span className="relative z-10 mt-1 line-clamp-2 text-xs font-medium opacity-90">{source.section}</span>
    </button>
  );
}

function AnswerText({ text, sources, onOpenSource }) {
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="flex flex-col gap-3 text-[15px] font-medium leading-relaxed">
      {blocks.map((block, index) => {
        const lines = block.split("\n");
        const isList = lines.every((line) => /^\s*([-*]|\d+\.)\s+/.test(line));
        if (isList) {
          return (
            <ul key={index} className="flex list-disc flex-col gap-1 pl-5">
              {lines.map((line, lineIndex) => (
                <li key={lineIndex}>
                  <Inline text={line.replace(/^\s*([-*]|\d+\.)\s+/, "")} sources={sources} onOpenSource={onOpenSource} />
                </li>
              ))}
            </ul>
          );
        }
        return (
          <p key={index} className="whitespace-pre-line">
            <Inline text={block} sources={sources} onOpenSource={onOpenSource} />
          </p>
        );
      })}
    </div>
  );
}

function Inline({ text, sources, onOpenSource }) {
  return text.split(/(\[\d+\]|\*\*[^*]+\*\*)/).map((part, index) => {
    const citation = part.match(/^\[(\d+)\]$/);
    if (citation && sources[citation[1]]) {
      const source = sources[citation[1]];
      return (
        <button
          key={index}
          type="button"
          onClick={() => onOpenSource(source)}
          aria-label={`Voir la source ${source.id} : ${source.document}`}
          className="btn-press relative mx-0.5 inline-flex h-6 min-w-6 items-center justify-center rounded-lg px-1.5 align-baseline text-xs font-black tabular-nums text-white before:absolute before:-inset-2.5 before:content-['']"
          style={{ background: "var(--gradient-tile)" }}
        >
          {source.id}
        </button>
      );
    }
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={index} className="font-black">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

function AnswerLoading() {
  return (
    <div className="glass-panel rounded-[32px] p-6 md:p-8">
      <div className="progress-bar mb-3" />
      <p className="label-meta mb-5 flex items-center gap-2">
        <BookOpen className="h-3.5 w-3.5" aria-hidden />
        Recherche dans vos documents…
      </p>
      <div className="flex flex-col gap-3">
        <div className="skeleton h-4 w-full" />
        <div className="skeleton h-4 w-11/12" />
        <div className="skeleton h-4 w-2/3" />
      </div>
    </div>
  );
}

function AskSkeleton() {
  return (
    <section className="mx-auto flex max-w-3xl flex-col items-center gap-4 pt-14" aria-label="Chargement">
      <div className="skeleton h-14 w-4/5" />
      <div className="skeleton h-5 w-3/5" />
      <div className="skeleton mt-6 h-[70px] w-full !rounded-full" />
    </section>
  );
}

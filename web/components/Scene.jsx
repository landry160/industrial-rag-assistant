export default function Scene() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden>
      <div className="absolute inset-0 bg-gradient-to-br from-slate-100 via-white to-slate-50 opacity-90 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950" />
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />
      <div className="grain" />
    </div>
  );
}

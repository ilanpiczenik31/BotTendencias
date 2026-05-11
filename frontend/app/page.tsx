"use client";

import { useEffect, useRef, useState } from "react";
import { api, Stats, Report, Run } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import Link from "next/link";
import { Play, RefreshCw, TrendingUp, Package, Store, Clock, ArrowRight, Sparkles, CheckCircle, XCircle, Loader2, Settings2 } from "lucide-react";
import RunConfigModal from "@/components/RunConfigModal";

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [triggering, setTriggering] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showConfig, setShowConfig] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isRunning = stats?.last_run_status === "running" || stats?.last_run_status === "pending";

  async function loadData(silent = false) {
    if (!silent) setLoading(true);
    try {
      const [s, r, rs] = await Promise.allSettled([
        api.getStats(), api.getLatestReport(), api.getRuns(5),
      ]);
      if (s.status === "fulfilled") setStats(s.value);
      if (r.status === "fulfilled") setReport(r.value);
      if (rs.status === "fulfilled") setRuns(rs.value);
    } finally { if (!silent) setLoading(false); }
  }

  // Auto-poll every 10s while a run is active
  useEffect(() => {
    if (isRunning) {
      pollRef.current = setInterval(() => loadData(true), 10000);
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [isRunning]);

  useEffect(() => { loadData(); }, []);

  async function handleTrigger(config?: { store: string; sections: any[] }[] | null) {
    setShowConfig(false);
    setTriggering(true);
    try {
      await api.triggerRun(config ?? undefined);
      setTimeout(() => loadData(true), 3000);
    } catch { /* ignore */ }
    finally { setTriggering(false); }
  }

  return (
    <div className="space-y-8">
      {showConfig && (
        <RunConfigModal onClose={() => setShowConfig(false)} onTrigger={handleTrigger} />
      )}
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-neutral-500 mt-0.5 text-sm">Tendencias de moda europea, actualizadas cada lunes.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => loadData()} disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-sm text-neutral-400 transition-colors disabled:opacity-50">
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} /> Actualizar
          </button>
          <button onClick={() => setShowConfig(true)} disabled={triggering || isRunning}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-sm text-neutral-300 transition-colors disabled:opacity-50">
            <Settings2 size={13} /> Configurar
          </button>
          <button onClick={() => handleTrigger(null)} disabled={triggering || isRunning}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-white hover:bg-neutral-100 text-sm text-neutral-900 font-semibold transition-colors disabled:opacity-60">
            <Play size={13} fill="currentColor" />
            {triggering ? "Iniciando..." : "Correr ahora"}
          </button>
        </div>
      </div>

      {/* Run status banner */}
      {isRunning && (
        <div className="rounded-lg bg-blue-950/50 border border-blue-800/40 px-4 py-3 flex items-center gap-3">
          <Loader2 size={15} className="animate-spin text-blue-400 shrink-0" />
          <div className="flex-1">
            <p className="text-sm text-blue-300 font-medium">Corrida en progreso...</p>
            <p className="text-xs text-blue-600 mt-0.5">Scrapeando las 8 tiendas. Esta página se actualiza sola cada 10 segundos.</p>
          </div>
        </div>
      )}
      {!isRunning && stats?.last_run_status === "completed" && runs[0]?.status === "completed" && (
        <div className="rounded-lg bg-emerald-950/40 border border-emerald-800/30 px-4 py-3 flex items-center gap-3">
          <CheckCircle size={15} className="text-emerald-500 shrink-0" />
          <p className="text-sm text-emerald-400">
            Última corrida completada — {stats.last_run_date ? format(new Date(stats.last_run_date), "dd MMM · HH:mm", { locale: es }) : ""}
          </p>
        </div>
      )}
      {!isRunning && stats?.last_run_status === "failed" && (
        <div className="rounded-lg bg-red-950/40 border border-red-800/30 px-4 py-3 flex items-center gap-3">
          <XCircle size={15} className="text-red-500 shrink-0" />
          <p className="text-sm text-red-400">La última corrida falló. Revisá los logs en Railway o volvé a correr.</p>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard icon={<Clock size={15} />} label="Corridas" value={stats?.total_runs ?? "—"} />
        <StatCard icon={<Package size={15} />} label="Productos" value={stats?.total_products?.toLocaleString("es") ?? "—"} />
        <StatCard icon={<Store size={15} />} label="Tiendas" value={stats?.total_stores ?? "—"} />
        <StatCard
          icon={<TrendingUp size={15} />} label="Último run"
          value={stats?.last_run_date ? format(new Date(stats.last_run_date), "dd MMM", { locale: es }) : "—"}
          sub={stats?.last_run_status}
        />
      </div>

      {/* Latest report */}
      {report ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Sparkles size={15} className="text-amber-400" /> Reporte más reciente
            </h2>
            <span className="text-xs text-neutral-600">
              {format(new Date(report.run_date), "EEEE d 'de' MMMM", { locale: es })}
            </span>
          </div>

          <div className="rounded-xl border border-neutral-800 bg-neutral-900/50 p-5 space-y-4">
            <p className="text-neutral-300 leading-relaxed text-sm">{report.summary}</p>

            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <TrendPills title="Colores" items={report.top_trends?.colors} pill="bg-pink-950 text-pink-300" />
              <TrendPills title="Estilos" items={report.top_trends?.styles} pill="bg-purple-950 text-purple-300" />
              <TrendPills title="Prendas" items={report.top_trends?.categories} pill="bg-blue-950 text-blue-300" />
              <TrendPills title="Keywords" items={report.top_trends?.keywords?.slice(0, 6)} pill="bg-emerald-950 text-emerald-300" />
            </div>

            {report.comparison_vs_prev?.argentina_recommendation && (
              <div className="rounded-lg bg-amber-950/40 border border-amber-800/40 p-4">
                <p className="text-xs font-semibold text-amber-400 uppercase tracking-widest mb-1.5">Para Argentina</p>
                <p className="text-sm text-amber-100/90 leading-relaxed">{report.comparison_vs_prev.argentina_recommendation}</p>
              </div>
            )}

            {report.comparison_vs_prev?.store_highlights && report.comparison_vs_prev.store_highlights.length > 0 && (
              <div className="grid sm:grid-cols-2 gap-2">
                {report.comparison_vs_prev.store_highlights.map((h, i) => (
                  <div key={i} className="rounded-lg bg-neutral-800/60 px-3 py-2.5 text-xs">
                    <span className="font-semibold text-white">{h.store}</span>
                    <span className="text-neutral-400"> — {h.highlight}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-4">
            <Link href="/trends" className="flex items-center gap-1 text-sm text-neutral-500 hover:text-white transition-colors">
              Ver tendencias <ArrowRight size={13} />
            </Link>
            <Link href="/history" className="flex items-center gap-1 text-sm text-neutral-500 hover:text-white transition-colors">
              Ver histórico <ArrowRight size={13} />
            </Link>
          </div>
        </div>
      ) : !loading ? (
        <div className="rounded-xl border border-dashed border-neutral-800 p-16 text-center">
          <p className="text-neutral-600 text-sm">No hay reportes todavía.</p>
          <p className="text-neutral-700 text-xs mt-1">Hacé clic en <strong className="text-neutral-500">Correr ahora</strong> para generar el primero.</p>
        </div>
      ) : null}

      {/* Recent runs */}
      {runs.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wide mb-3">Corridas recientes</h2>
          <div className="space-y-1.5">
            {runs.map((run) => (
              <Link key={run.id} href={`/runs/${run.id}`}
                className="flex items-center justify-between rounded-lg bg-neutral-900 border border-neutral-800/60 px-4 py-2.5 hover:border-neutral-700 transition-colors group">
                <div className="flex items-center gap-3">
                  <StatusDot status={run.status} />
                  <span className="text-sm text-neutral-300">
                    {format(new Date(run.run_date), "dd MMM yyyy · HH:mm", { locale: es })}
                  </span>
                  <span className="text-xs text-neutral-600">{run.triggered_by}</span>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusStyle(run.status)}`}>
                  {run.status}
                </span>
              </Link>
            ))}
          </div>
          <Link href="/runs" className="mt-3 inline-flex items-center gap-1 text-sm text-neutral-600 hover:text-neutral-400 transition-colors">
            Ver todas <ArrowRight size={12} />
          </Link>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string | number; sub?: string | null }) {
  return (
    <div className="rounded-xl bg-neutral-900 border border-neutral-800/60 p-4">
      <div className="flex items-center gap-1.5 text-neutral-600 mb-2 text-xs">{icon} {label}</div>
      <p className="text-2xl font-bold text-white tracking-tight">{value}</p>
      {sub && <p className="text-xs text-neutral-600 mt-0.5 capitalize">{sub}</p>}
    </div>
  );
}

function TrendPills({ title, items, pill }: { title: string; items?: string[]; pill: string }) {
  if (!items?.length) return null;
  return (
    <div>
      <p className="text-xs font-semibold text-neutral-600 uppercase tracking-widest mb-2">{title}</p>
      <div className="flex flex-wrap gap-1">
        {items.map((t, i) => (
          <span key={i} className={`text-xs px-2 py-0.5 rounded-full font-medium ${pill}`}>{t}</span>
        ))}
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const c: Record<string, string> = {
    completed: "bg-emerald-500", running: "bg-blue-400 animate-pulse",
    failed: "bg-red-500", pending: "bg-yellow-500",
  };
  return <span className={`w-1.5 h-1.5 rounded-full ${c[status] ?? "bg-neutral-500"}`} />;
}

function statusStyle(s: string) {
  const m: Record<string, string> = {
    completed: "bg-emerald-950 text-emerald-400",
    running: "bg-blue-950 text-blue-400",
    failed: "bg-red-950 text-red-400",
    pending: "bg-yellow-950 text-yellow-400",
  };
  return m[s] ?? "bg-neutral-800 text-neutral-500";
}

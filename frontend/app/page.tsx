"use client";

import { useEffect, useRef, useState } from "react";
import { api, Stats, Report, Run } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import Link from "next/link";
import { Play, RefreshCw, Settings2, CheckCircle, XCircle, Loader2, ArrowRight, TrendingUp } from "lucide-react";
import RunConfigModal from "@/components/RunConfigModal";

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [triggering, setTriggering] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showConfig, setShowConfig] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isRunning = stats?.last_run_status === "running" || stats?.last_run_status === "pending";
  const current = reports[0] ?? null;
  const previous = reports[1] ?? null;

  async function loadData(silent = false) {
    if (!silent) setLoading(true);
    try {
      const [s, rs, ru] = await Promise.allSettled([
        api.getStats(),
        api.getReports(2),
        api.getRuns(5),
      ]);
      if (s.status === "fulfilled") setStats(s.value);
      if (rs.status === "fulfilled") setReports(rs.value);
      if (ru.status === "fulfilled") setRuns(ru.value);
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => {
    if (isRunning) {
      pollRef.current = setInterval(() => loadData(true), 10000);
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [isRunning]);

  useEffect(() => { loadData(); }, []);

  async function handleTrigger(config?: any) {
    setShowConfig(false);
    setTriggering(true);
    try {
      await api.triggerRun(config ?? undefined);
      setTimeout(() => loadData(true), 3000);
    } catch { }
    finally { setTriggering(false); }
  }

  return (
    <div className="space-y-6">
      {showConfig && <RunConfigModal onClose={() => setShowConfig(false)} onTrigger={handleTrigger} />}

      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-white">Dashboard</h1>
          <p className="text-neutral-600 text-sm mt-0.5">Zara · H&M — actualizado cada lunes</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => loadData()} disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neutral-900 border border-neutral-800 text-sm text-neutral-400 hover:text-white transition-colors disabled:opacity-50">
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Actualizar
          </button>
          <button onClick={() => setShowConfig(true)} disabled={triggering || isRunning}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neutral-900 border border-neutral-800 text-sm text-neutral-300 hover:text-white transition-colors disabled:opacity-50">
            <Settings2 size={12} /> Configurar
          </button>
          <button onClick={() => handleTrigger(null)} disabled={triggering || isRunning}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-white text-neutral-900 text-sm font-semibold hover:bg-neutral-100 transition-colors disabled:opacity-60">
            <Play size={12} fill="currentColor" />
            {triggering ? "Iniciando..." : "Correr ahora"}
          </button>
        </div>
      </div>

      {/* Status */}
      {isRunning && (
        <div className="rounded-lg bg-blue-950/40 border border-blue-800/30 px-4 py-3 flex items-center gap-3">
          <Loader2 size={14} className="animate-spin text-blue-400 shrink-0" />
          <p className="text-sm text-blue-300">Corrida en progreso — se actualiza cada 10 segundos</p>
        </div>
      )}
      {!isRunning && stats?.last_run_status === "failed" && (
        <div className="rounded-lg bg-red-950/40 border border-red-800/30 px-4 py-3 flex items-center gap-3">
          <XCircle size={14} className="text-red-500 shrink-0" />
          <p className="text-sm text-red-400">La última corrida falló</p>
        </div>
      )}

      {/* Stats strip */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Corridas", value: stats?.total_runs ?? "—" },
          { label: "Productos", value: stats?.total_products?.toLocaleString("es") ?? "—" },
          { label: "Tiendas activas", value: stats?.total_stores ?? "—" },
          {
            label: "Última corrida",
            value: stats?.last_run_date ? format(new Date(stats.last_run_date), "dd MMM", { locale: es }) : "—",
            sub: stats?.last_run_status,
          },
        ].map((s) => (
          <div key={s.label} className="rounded-xl bg-neutral-900 border border-neutral-800/60 px-4 py-3">
            <p className="text-xs text-neutral-600 mb-1">{s.label}</p>
            <p className="text-xl font-bold text-white">{s.value}</p>
            {s.sub && <p className="text-xs text-neutral-600 capitalize mt-0.5">{s.sub}</p>}
          </div>
        ))}
      </div>

      {/* Esta semana vs semana anterior */}
      {current ? (
        <div className="grid md:grid-cols-2 gap-4">
          {/* Esta semana */}
          <div className="rounded-xl border border-neutral-800/60 bg-neutral-900/50 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-neutral-500 uppercase tracking-widest">Esta semana</p>
              <span className="text-xs text-neutral-600">
                {format(new Date(current.run_date), "dd MMM", { locale: es })}
              </span>
            </div>
            <p className="text-sm text-neutral-300 leading-relaxed">{current.summary}</p>
            {current.top_trends?.top_products && current.top_trends.top_products.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs text-neutral-600 uppercase tracking-widest">Top productos</p>
                {current.top_trends.top_products.slice(0, 3).map((p, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-xs font-bold text-amber-600 w-4">{i + 1}</span>
                    <span className="text-sm text-neutral-300">{p}</span>
                  </div>
                ))}
              </div>
            )}
            <div className="flex flex-wrap gap-1 pt-1">
              {current.top_trends?.colors?.slice(0, 3).map((c, i) => (
                <span key={i} className="text-xs bg-pink-950/60 text-pink-400 px-2 py-0.5 rounded-full">{c}</span>
              ))}
              {current.top_trends?.styles?.slice(0, 2).map((s, i) => (
                <span key={i} className="text-xs bg-purple-950/60 text-purple-400 px-2 py-0.5 rounded-full">{s}</span>
              ))}
            </div>
          </div>

          {/* Semana anterior */}
          <div className="rounded-xl border border-neutral-800/40 bg-neutral-900/30 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-neutral-600 uppercase tracking-widest">Semana anterior</p>
              {previous && (
                <span className="text-xs text-neutral-700">
                  {format(new Date(previous.run_date), "dd MMM", { locale: es })}
                </span>
              )}
            </div>
            {previous ? (
              <>
                <p className="text-sm text-neutral-500 leading-relaxed">{previous.summary}</p>
                <div className="flex flex-wrap gap-1 pt-1">
                  {previous.top_trends?.colors?.slice(0, 3).map((c, i) => (
                    <span key={i} className="text-xs bg-neutral-800 text-neutral-600 px-2 py-0.5 rounded-full">{c}</span>
                  ))}
                  {previous.top_trends?.styles?.slice(0, 2).map((s, i) => (
                    <span key={i} className="text-xs bg-neutral-800 text-neutral-600 px-2 py-0.5 rounded-full">{s}</span>
                  ))}
                </div>
                {current.comparison_vs_prev?.vs_last_week && (
                  <div className="rounded-lg bg-neutral-800/60 px-3 py-2 mt-1">
                    <p className="text-xs text-neutral-500 flex items-center gap-1.5">
                      <TrendingUp size={11} className="text-emerald-500" />
                      {current.comparison_vs_prev.vs_last_week}
                    </p>
                  </div>
                )}
              </>
            ) : (
              <p className="text-sm text-neutral-700">No hay corrida anterior todavía.</p>
            )}
          </div>
        </div>
      ) : !loading ? (
        <div className="rounded-xl border border-dashed border-neutral-800 p-16 text-center">
          <p className="text-neutral-600 text-sm">No hay reportes todavía.</p>
          <p className="text-neutral-700 text-xs mt-1">Hacé clic en <strong className="text-neutral-500">Correr ahora</strong> para generar el primero.</p>
        </div>
      ) : null}

      {/* Para Argentina */}
      {current?.comparison_vs_prev?.argentina_recommendation && (
        <div className="rounded-xl border border-neutral-700/40 bg-neutral-900/50 px-5 py-4">
          <p className="text-xs font-semibold text-neutral-500 uppercase tracking-widest mb-2">Para Argentina</p>
          <p className="text-sm text-neutral-300 leading-relaxed">{current.comparison_vs_prev.argentina_recommendation}</p>
        </div>
      )}

      {/* Links */}
      <div className="flex gap-4">
        <Link href="/trends" className="flex items-center gap-1 text-sm text-neutral-600 hover:text-white transition-colors">
          Ver productos <ArrowRight size={12} />
        </Link>
        <Link href="/analysis" className="flex items-center gap-1 text-sm text-neutral-600 hover:text-white transition-colors">
          Ver análisis completo <ArrowRight size={12} />
        </Link>
        <Link href="/runs" className="flex items-center gap-1 text-sm text-neutral-600 hover:text-white transition-colors">
          Historial <ArrowRight size={12} />
        </Link>
      </div>
    </div>
  );
}

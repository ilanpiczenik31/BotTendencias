"use client";

import { useEffect, useState } from "react";
import { api, Stats, Report, Run } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import Link from "next/link";
import { Play, RefreshCw, TrendingUp, Package, Store, Activity } from "lucide-react";

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadData() {
    setLoading(true);
    try {
      const [s, r, rs] = await Promise.allSettled([
        api.getStats(),
        api.getLatestReport(),
        api.getRuns(5),
      ]);
      if (s.status === "fulfilled") setStats(s.value);
      if (r.status === "fulfilled") setReport(r.value);
      if (rs.status === "fulfilled") setRuns(rs.value);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, []);

  async function handleTrigger() {
    setTriggering(true);
    setTriggerMsg("");
    try {
      await api.triggerRun();
      setTriggerMsg("Corrida iniciada. Puede tardar varios minutos...");
      setTimeout(loadData, 5000);
    } catch {
      setTriggerMsg("Error al iniciar la corrida.");
    } finally {
      setTriggering(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-neutral-400 mt-1">Tendencias de moda europea, actualizadas cada lunes.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-sm text-neutral-300 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Actualizar
          </button>
          <button
            onClick={handleTrigger}
            disabled={triggering}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white hover:bg-neutral-100 text-sm text-neutral-900 font-medium transition-colors disabled:opacity-60"
          >
            <Play size={14} />
            {triggering ? "Iniciando..." : "Correr ahora"}
          </button>
        </div>
      </div>

      {triggerMsg && (
        <div className="rounded-lg bg-blue-950 border border-blue-800 px-4 py-3 text-sm text-blue-300">
          {triggerMsg}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={<Activity size={18} />} label="Corridas totales" value={stats?.total_runs ?? "—"} />
        <StatCard icon={<Package size={18} />} label="Productos scrapeados" value={stats?.total_products?.toLocaleString("es") ?? "—"} />
        <StatCard icon={<Store size={18} />} label="Tiendas activas" value={stats?.total_stores ?? "—"} />
        <StatCard
          icon={<TrendingUp size={18} />}
          label="Última corrida"
          value={stats?.last_run_date ? format(new Date(stats.last_run_date), "dd MMM", { locale: es }) : "—"}
          sub={stats?.last_run_status}
        />
      </div>

      {/* Latest report */}
      {report ? (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Reporte más reciente</h2>
            <span className="text-xs text-neutral-500">
              {format(new Date(report.run_date), "EEEE d 'de' MMMM yyyy", { locale: es })}
            </span>
          </div>

          <p className="text-neutral-300 leading-relaxed text-sm">{report.summary}</p>

          <div className="grid md:grid-cols-2 gap-6">
            <TrendSection title="Colores en tendencia" items={report.top_trends?.colors} color="bg-pink-900 text-pink-200" />
            <TrendSection title="Estilos predominantes" items={report.top_trends?.styles} color="bg-purple-900 text-purple-200" />
            <TrendSection title="Prendas más presentes" items={report.top_trends?.categories} color="bg-blue-900 text-blue-200" />
            <TrendSection title="Keywords de la semana" items={report.top_trends?.keywords?.slice(0, 8)} color="bg-emerald-900 text-emerald-200" />
          </div>

          {report.comparison_vs_prev?.argentina_recommendation && (
            <div className="rounded-lg bg-amber-950 border border-amber-800 p-4">
              <p className="text-xs font-medium text-amber-400 uppercase tracking-wide mb-1">Recomendación para Argentina</p>
              <p className="text-sm text-amber-100">{report.comparison_vs_prev.argentina_recommendation}</p>
            </div>
          )}

          {report.comparison_vs_prev?.store_highlights && report.comparison_vs_prev.store_highlights.length > 0 && (
            <div>
              <p className="text-xs font-medium text-neutral-400 uppercase tracking-wide mb-3">Highlights por tienda</p>
              <div className="grid sm:grid-cols-2 gap-2">
                {report.comparison_vs_prev.store_highlights.map((h, i) => (
                  <div key={i} className="rounded-lg bg-neutral-800 px-3 py-2">
                    <span className="text-xs font-medium text-white">{h.store}: </span>
                    <span className="text-xs text-neutral-400">{h.highlight}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <Link href="/trends" className="text-sm text-neutral-400 hover:text-white underline underline-offset-2">
              Ver tendencias por tienda →
            </Link>
            <Link href="/history" className="text-sm text-neutral-400 hover:text-white underline underline-offset-2">
              Ver histórico →
            </Link>
          </div>
        </div>
      ) : !loading ? (
        <div className="rounded-xl border border-dashed border-neutral-700 p-12 text-center">
          <p className="text-neutral-500 text-sm">No hay reportes todavía. Hace clic en <strong className="text-neutral-300">Correr ahora</strong> para generar el primero.</p>
        </div>
      ) : null}

      {/* Recent runs */}
      {runs.length > 0 && (
        <div>
          <h2 className="text-base font-semibold text-white mb-3">Corridas recientes</h2>
          <div className="space-y-2">
            {runs.map((run) => (
              <Link
                key={run.id}
                href={`/runs/${run.id}`}
                className="flex items-center justify-between rounded-lg bg-neutral-900 border border-neutral-800 px-4 py-3 hover:border-neutral-600 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <StatusDot status={run.status} />
                  <span className="text-sm text-neutral-300">
                    {format(new Date(run.run_date), "dd MMM yyyy HH:mm", { locale: es })}
                  </span>
                  <span className="text-xs text-neutral-600">{run.triggered_by}</span>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusStyle(run.status)}`}>
                  {run.status}
                </span>
              </Link>
            ))}
          </div>
          <Link href="/runs" className="mt-3 inline-block text-sm text-neutral-500 hover:text-neutral-300">
            Ver todas →
          </Link>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string | number; sub?: string | null }) {
  return (
    <div className="rounded-xl bg-neutral-900 border border-neutral-800 p-4">
      <div className="flex items-center gap-2 text-neutral-500 mb-2 text-sm">{icon} {label}</div>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-neutral-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function TrendSection({ title, items, color }: { title: string; items?: string[]; color: string }) {
  if (!items?.length) return null;
  return (
    <div>
      <p className="text-xs font-medium text-neutral-400 uppercase tracking-wide mb-2">{title}</p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => (
          <span key={i} className={`text-xs px-2 py-0.5 rounded-full font-medium ${color}`}>{item}</span>
        ))}
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: "bg-emerald-500",
    running: "bg-blue-500 animate-pulse",
    failed: "bg-red-500",
    pending: "bg-yellow-500",
  };
  return <span className={`w-2 h-2 rounded-full ${colors[status] ?? "bg-neutral-500"}`} />;
}

function statusStyle(status: string) {
  const s: Record<string, string> = {
    completed: "bg-emerald-900 text-emerald-300",
    running: "bg-blue-900 text-blue-300",
    failed: "bg-red-900 text-red-300",
    pending: "bg-yellow-900 text-yellow-300",
  };
  return s[status] ?? "bg-neutral-800 text-neutral-400";
}

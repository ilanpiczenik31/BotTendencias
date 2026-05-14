"use client";

import { useEffect, useState } from "react";
import { api, Run, TrendAnalysis, Report } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";

export default function AnalysisPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [analyses, setAnalyses] = useState<TrendAnalysis[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getRuns(20).then(rs => {
      const completed = rs.filter(r => r.status === "completed");
      setRuns(completed);
      if (completed[0]) setSelectedRun(completed[0]);
    });
  }, []);

  useEffect(() => {
    if (!selectedRun) return;
    setLoading(true);
    Promise.allSettled([
      api.getRunAnalyses(selectedRun.id),
      api.getReportByRun(selectedRun.id),
    ]).then(([a, r]) => {
      if (a.status === "fulfilled") setAnalyses(a.value);
      if (r.status === "fulfilled") setReport(r.value);
    }).finally(() => setLoading(false));
  }, [selectedRun]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-white">Análisis</h1>
          <p className="text-neutral-600 text-sm mt-0.5">Análisis de IA por corrida y tienda</p>
        </div>
        <select
          value={selectedRun?.id ?? ""}
          onChange={e => setSelectedRun(runs.find(r => r.id === Number(e.target.value)) ?? null)}
          className="bg-neutral-900 border border-neutral-800 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none">
          {runs.map(r => (
            <option key={r.id} value={r.id}>
              {format(new Date(r.run_date), "dd MMM yyyy · HH:mm", { locale: es })}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="text-center py-20 text-neutral-700 text-sm">Cargando...</div>
      ) : (
        <div className="space-y-5">
          {/* Reporte global */}
          {report && (
            <div className="rounded-xl border border-neutral-800/60 bg-neutral-900/50 p-5 space-y-4">
              <p className="text-xs font-semibold text-neutral-500 uppercase tracking-widest">Reporte global</p>
              <p className="text-sm text-neutral-300 leading-relaxed">{report.summary}</p>

              <div className="grid sm:grid-cols-3 gap-4">
                <PillGroup title="Top colores" tags={report.top_trends?.colors?.slice(0, 3)} cls="bg-pink-950/60 text-pink-400" />
                <PillGroup title="Top estilos" tags={report.top_trends?.styles?.slice(0, 3)} cls="bg-purple-950/60 text-purple-400" />
                <PillGroup title="Top prendas" tags={report.top_trends?.categories?.slice(0, 3)} cls="bg-blue-950/60 text-blue-400" />
              </div>

              {report.top_trends?.top_products && report.top_trends.top_products.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-xs font-semibold text-neutral-600 uppercase tracking-widest">Top productos globales</p>
                  {report.top_trends.top_products.slice(0, 3).map((p, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-sm font-bold text-amber-600 w-4">{i + 1}</span>
                      <span className="text-sm text-neutral-400">{p}</span>
                    </div>
                  ))}
                </div>
              )}

              {report.comparison_vs_prev?.argentina_recommendation && (
                <div className="rounded-lg bg-neutral-800/60 px-4 py-3">
                  <p className="text-xs font-semibold text-neutral-500 mb-1">Para Argentina</p>
                  <p className="text-sm text-neutral-300 leading-relaxed">{report.comparison_vs_prev.argentina_recommendation}</p>
                </div>
              )}

              {report.comparison_vs_prev?.vs_last_week && (
                <p className="text-xs text-neutral-600 italic">{report.comparison_vs_prev.vs_last_week}</p>
              )}
            </div>
          )}

          {/* Por tienda */}
          {analyses.map(a => (
            <div key={a.store} className="rounded-xl border border-neutral-800/60 bg-neutral-900/50 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-white">{a.store}</p>
                {a.trends.trend_score != null && (
                  <span className="text-xs bg-neutral-800 text-neutral-400 px-2 py-0.5 rounded-full">
                    {a.trends.trend_score}/10
                  </span>
                )}
              </div>

              <p className="text-sm text-neutral-400 leading-relaxed">{a.summary}</p>

              {a.trends.top_products && a.trends.top_products.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-neutral-600 uppercase tracking-widest">Top productos</p>
                  {a.trends.top_products.slice(0, 3).map((p, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-xs font-bold text-amber-600 w-4">{i + 1}</span>
                      <span className="text-sm text-neutral-400">{p}</span>
                    </div>
                  ))}
                </div>
              )}

              <div className="grid sm:grid-cols-3 gap-3">
                <PillGroup title="Colores" tags={a.trends.colors?.slice(0, 3)} cls="bg-pink-950/60 text-pink-400" />
                <PillGroup title="Estilos" tags={a.trends.styles?.slice(0, 3)} cls="bg-purple-950/60 text-purple-400" />
                <PillGroup title="Prendas" tags={a.trends.categories?.slice(0, 3)} cls="bg-blue-950/60 text-blue-400" />
              </div>

              {a.trends.price_range?.min != null && a.trends.price_range?.max != null && (
                <p className="text-xs text-neutral-600">
                  Precio: <span className="text-neutral-500">{a.trends.price_range.min} – {a.trends.price_range.max} {a.trends.price_range.currency}</span>
                </p>
              )}
            </div>
          ))}

          {!report && analyses.length === 0 && !loading && (
            <div className="text-center py-20 text-neutral-700 text-sm">No hay análisis para esta corrida.</div>
          )}
        </div>
      )}
    </div>
  );
}

function PillGroup({ title, tags, cls }: { title: string; tags?: string[]; cls: string }) {
  if (!tags?.length) return null;
  return (
    <div>
      <p className="text-xs font-semibold text-neutral-600 uppercase tracking-widest mb-1.5">{title}</p>
      <div className="flex flex-wrap gap-1">
        {tags.map((t, i) => <span key={i} className={`text-xs px-2 py-0.5 rounded-full ${cls}`}>{t}</span>)}
      </div>
    </div>
  );
}

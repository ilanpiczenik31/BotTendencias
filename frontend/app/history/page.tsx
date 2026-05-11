"use client";

import { useEffect, useState } from "react";
import { api, Report } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import Link from "next/link";

export default function HistoryPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Report | null>(null);

  useEffect(() => {
    api.getReports(20).then((rs) => {
      setReports(rs);
      if (rs.length > 0) setSelected(rs[0]);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-20 text-neutral-500 text-sm">Cargando...</div>;

  if (!reports.length) {
    return (
      <div className="text-center py-20">
        <p className="text-neutral-500 text-sm">No hay reportes todavía.</p>
        <Link href="/" className="mt-4 inline-block text-sm text-neutral-400 hover:text-white underline">
          Ir al dashboard →
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Histórico</h1>
        <p className="text-neutral-400 mt-1">Comparación semana a semana de tendencias.</p>
      </div>

      <div className="grid md:grid-cols-[280px_1fr] gap-6">
        {/* Sidebar: list of reports */}
        <div className="space-y-2">
          <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-3">Semanas</p>
          {reports.map((r) => (
            <button
              key={r.id}
              onClick={() => setSelected(r)}
              className={`w-full text-left rounded-lg px-3 py-2.5 transition-colors ${
                selected?.id === r.id
                  ? "bg-white text-neutral-900"
                  : "bg-neutral-900 border border-neutral-800 text-neutral-300 hover:border-neutral-600"
              }`}
            >
              <p className="text-sm font-medium">
                {format(new Date(r.run_date), "dd MMM yyyy", { locale: es })}
              </p>
              <p className={`text-xs mt-0.5 ${selected?.id === r.id ? "text-neutral-600" : "text-neutral-500"}`}>
                Run #{r.run_id}
              </p>
            </button>
          ))}
        </div>

        {/* Detail */}
        {selected && (
          <div className="space-y-5">
            <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h2 className="text-xl font-bold text-white">
                  Semana del {format(new Date(selected.run_date), "dd 'de' MMMM yyyy", { locale: es })}
                </h2>
                <Link
                  href={`/runs/${selected.run_id}`}
                  className="text-xs text-neutral-400 hover:text-white underline"
                >
                  Ver corrida →
                </Link>
              </div>

              <p className="text-neutral-300 text-sm leading-relaxed">{selected.summary}</p>

              {/* Top trends */}
              <div className="grid sm:grid-cols-2 gap-4">
                <TagGroup title="Top colores" tags={selected.top_trends?.colors} colorClass="bg-pink-950 text-pink-300" />
                <TagGroup title="Top estilos" tags={selected.top_trends?.styles} colorClass="bg-purple-950 text-purple-300" />
                <TagGroup title="Top prendas" tags={selected.top_trends?.categories} colorClass="bg-blue-950 text-blue-300" />
                <TagGroup title="Keywords" tags={selected.top_trends?.keywords?.slice(0, 8)} colorClass="bg-emerald-950 text-emerald-300" />
              </div>
            </div>

            {/* vs last week */}
            {selected.comparison_vs_prev?.vs_last_week && (
              <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 space-y-2">
                <h3 className="text-sm font-semibold text-white">vs semana anterior</h3>
                <p className="text-sm text-neutral-400 leading-relaxed">{selected.comparison_vs_prev.vs_last_week}</p>
              </div>
            )}

            {/* Argentina recommendation */}
            {selected.comparison_vs_prev?.argentina_recommendation && (
              <div className="rounded-xl bg-amber-950 border border-amber-800 p-5 space-y-2">
                <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wide">Para Argentina</h3>
                <p className="text-sm text-amber-100 leading-relaxed">
                  {selected.comparison_vs_prev.argentina_recommendation}
                </p>
              </div>
            )}

            {/* Store highlights */}
            {selected.comparison_vs_prev?.store_highlights && selected.comparison_vs_prev.store_highlights.length > 0 && (
              <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 space-y-3">
                <h3 className="text-sm font-semibold text-white">Highlights por tienda</h3>
                <div className="grid sm:grid-cols-2 gap-2">
                  {selected.comparison_vs_prev.store_highlights.map((h, i) => (
                    <div key={i} className="rounded-lg bg-neutral-800 px-3 py-2">
                      <span className="text-xs font-medium text-white">{h.store}: </span>
                      <span className="text-xs text-neutral-400">{h.highlight}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function TagGroup({ title, tags, colorClass }: { title: string; tags?: string[]; colorClass: string }) {
  if (!tags?.length) return null;
  return (
    <div>
      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-2">{title}</p>
      <div className="flex flex-wrap gap-1.5">
        {tags.map((t, i) => (
          <span key={i} className={`text-xs px-2 py-0.5 rounded-full font-medium ${colorClass}`}>{t}</span>
        ))}
      </div>
    </div>
  );
}

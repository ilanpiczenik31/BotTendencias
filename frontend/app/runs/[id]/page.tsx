"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, Run, TrendAnalysis, Product, Report } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import Link from "next/link";

export default function RunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const runId = Number(id);

  const [run, setRun] = useState<Run | null>(null);
  const [analyses, setAnalyses] = useState<TrendAnalysis[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedStore, setSelectedStore] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([
      api.getRun(runId),
      api.getRunAnalyses(runId),
      api.getRunProducts(runId),
      api.getReportByRun(runId),
    ]).then(([r, a, p, rep]) => {
      if (r.status === "fulfilled") setRun(r.value);
      if (a.status === "fulfilled") setAnalyses(a.value);
      if (p.status === "fulfilled") setProducts(p.value);
      if (rep.status === "fulfilled") setReport(rep.value);
    }).finally(() => setLoading(false));
  }, [runId]);

  const storeNames = [...new Set(products.map((p) => ({ id: p.store_id, name: p.store })))];
  const filteredProducts = selectedStore
    ? products.filter((p) => p.store_id === selectedStore)
    : products;

  if (loading) return <div className="text-center py-20 text-neutral-500 text-sm">Cargando...</div>;
  if (!run) return <div className="text-center py-20 text-neutral-500 text-sm">Corrida no encontrada.</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <Link href="/runs" className="text-sm text-neutral-500 hover:text-neutral-300 mb-2 inline-block">← Corridas</Link>
          <h1 className="text-3xl font-bold text-white">Corrida #{runId}</h1>
          <p className="text-neutral-400 mt-1">
            {format(new Date(run.run_date), "EEEE d 'de' MMMM yyyy, HH:mm", { locale: es })}
            {" · "}{run.triggered_by} · <StatusBadge status={run.status} />
          </p>
        </div>
      </div>

      {/* Report */}
      {report && (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white">Reporte de la semana</h2>
          <p className="text-neutral-300 text-sm leading-relaxed">{report.summary}</p>
          <div className="grid sm:grid-cols-2 gap-4">
            <TagGroup title="Top colores" tags={report.top_trends?.colors} colorClass="bg-pink-950 text-pink-300" />
            <TagGroup title="Top estilos" tags={report.top_trends?.styles} colorClass="bg-purple-950 text-purple-300" />
          </div>
          {report.comparison_vs_prev?.argentina_recommendation && (
            <div className="rounded-lg bg-amber-950 border border-amber-800 p-4">
              <p className="text-xs font-medium text-amber-400 mb-1">Para Argentina</p>
              <p className="text-sm text-amber-100">{report.comparison_vs_prev.argentina_recommendation}</p>
            </div>
          )}
        </div>
      )}

      {/* Store analyses */}
      {analyses.length > 0 && (
        <div>
          <h2 className="text-base font-semibold text-white mb-3">Análisis por tienda</h2>
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
            {analyses.map((a) => (
              <div key={a.store} className="rounded-xl border border-neutral-800 bg-neutral-900 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-white">{a.store}</h3>
                  <span className="text-xs bg-neutral-800 text-neutral-400 px-2 py-0.5 rounded-full">
                    {a.trends.trend_score ?? "?"}/10
                  </span>
                </div>
                <p className="text-xs text-neutral-400 leading-relaxed">{a.summary}</p>
                {a.trends.colors && a.trends.colors.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {a.trends.colors.slice(0, 5).map((c, i) => (
                      <span key={i} className="text-xs bg-pink-950 text-pink-300 px-1.5 py-0.5 rounded-full">{c}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Products */}
      {products.length > 0 && (
        <div>
          <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
            <h2 className="text-base font-semibold text-white">Productos ({products.length})</h2>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedStore(null)}
                className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${!selectedStore ? "bg-white text-neutral-900 font-medium" : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700"}`}
              >
                Todas
              </button>
              {[...new Map(products.map((p) => [p.store_id, p.store])).entries()].map(([sid, sname]) => (
                <button
                  key={sid}
                  onClick={() => setSelectedStore(sid === selectedStore ? null : sid)}
                  className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${selectedStore === sid ? "bg-white text-neutral-900 font-medium" : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700"}`}
                >
                  {sname}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
            {filteredProducts.slice(0, 80).map((p) => (
              <a
                key={p.id}
                href={p.product_url ?? "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="group rounded-xl overflow-hidden border border-neutral-800 bg-neutral-900 hover:border-neutral-600 transition-colors"
              >
                <div className="aspect-[3/4] bg-neutral-800 relative">
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-neutral-600 text-2xl">👗</div>
                  )}
                  <span className="absolute top-2 left-2 text-xs bg-black/70 text-neutral-300 px-2 py-0.5 rounded-full">
                    {p.section === "new_arrivals" ? "Nuevo" : p.section === "best_sellers" ? "Best seller" : "Trending"}
                  </span>
                </div>
                <div className="p-3">
                  <p className="text-xs text-neutral-500 mb-0.5">{p.store}</p>
                  <p className="text-sm text-neutral-200 line-clamp-2 leading-snug">{p.name}</p>
                  {p.price && <p className="text-sm font-medium text-white mt-1">{p.price} {p.currency}</p>}
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "text-emerald-400",
    running: "text-blue-400",
    failed: "text-red-400",
    pending: "text-yellow-400",
  };
  return <span className={`font-medium ${styles[status] ?? "text-neutral-400"}`}>{status}</span>;
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

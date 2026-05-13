"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, Run, TrendAnalysis, Product, Report } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import Link from "next/link";
import { ExternalLink } from "lucide-react";

const SECTION_LABELS: Record<string, string> = {
  new_arrivals_women: "Nuevo · Mujer",
  new_arrivals_men:   "Nuevo · Hombre",
  trending_women:     "Trends · Mujer",
  new_arrivals:       "Novedades",
  trending:           "Trending",
  best_sellers:       "Best seller",
};

const SECTION_ORDER = ["new_arrivals_women", "new_arrivals_men", "trending_women", "new_arrivals", "trending"];

export default function RunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const runId = Number(id);

  const [run, setRun] = useState<Run | null>(null);
  const [analyses, setAnalyses] = useState<TrendAnalysis[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedStore, setSelectedStore] = useState<number | null>(null);
  const [activeSection, setActiveSection] = useState<string>("");

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

  const storeProducts = selectedStore
    ? products.filter((p) => p.store_id === selectedStore)
    : products;

  const sectionCounts = storeProducts.reduce((acc, p) => {
    acc[p.section] = (acc[p.section] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Sections in display order, only ones with products
  const availableSections = [
    ...SECTION_ORDER.filter(s => sectionCounts[s] > 0),
    // Any sections not in SECTION_ORDER
    ...Object.keys(sectionCounts).filter(s => !SECTION_ORDER.includes(s) && sectionCounts[s] > 0),
  ];

  const currentSection = activeSection && availableSections.includes(activeSection)
    ? activeSection
    : availableSections[0] ?? "";

  const sectionProducts = currentSection
    ? storeProducts.filter(p => p.section === currentSection).slice(0, 20)
    : storeProducts.slice(0, 20);

  if (loading) return <div className="text-center py-20 text-neutral-500 text-sm">Cargando...</div>;
  if (!run) return <div className="text-center py-20 text-neutral-500 text-sm">Corrida no encontrada.</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link href="/runs" className="text-sm text-neutral-500 hover:text-neutral-300 mb-2 inline-block">← Corridas</Link>
        <h1 className="text-2xl font-bold text-white">Corrida #{runId}</h1>
        <p className="text-neutral-500 mt-1 text-sm">
          {format(new Date(run.run_date), "EEEE d 'de' MMMM yyyy, HH:mm", { locale: es })}
          {" · "}{run.triggered_by} · <StatusBadge status={run.status} />
        </p>
      </div>

      {/* Report */}
      {report && (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-5 space-y-4">
          <h2 className="text-sm font-semibold text-white">Reporte</h2>
          <p className="text-neutral-400 text-sm leading-relaxed">{report.summary}</p>

          {report.top_trends?.top_products && report.top_trends.top_products.length > 0 && (
            <div className="rounded-lg bg-amber-950/20 border border-amber-800/30 p-3 space-y-1.5">
              <p className="text-xs font-semibold text-amber-500 uppercase tracking-widest">Top productos</p>
              {report.top_trends.top_products.slice(0, 3).map((p, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-sm font-bold text-amber-600 w-4">{i + 1}</span>
                  <span className="text-sm text-amber-100/80">{p}</span>
                </div>
              ))}
            </div>
          )}

          <div className="grid sm:grid-cols-3 gap-3">
            <TagGroup title="Colores" tags={report.top_trends?.colors?.slice(0, 3)} colorClass="bg-pink-950 text-pink-300" />
            <TagGroup title="Estilos" tags={report.top_trends?.styles?.slice(0, 3)} colorClass="bg-purple-950 text-purple-300" />
            <TagGroup title="Prendas" tags={report.top_trends?.categories?.slice(0, 3)} colorClass="bg-blue-950 text-blue-300" />
          </div>

          {report.comparison_vs_prev?.argentina_recommendation && (
            <div className="rounded-lg bg-neutral-800/60 border border-neutral-700/40 p-3">
              <p className="text-xs font-medium text-neutral-500 mb-1">Para Argentina</p>
              <p className="text-sm text-neutral-300 leading-relaxed">{report.comparison_vs_prev.argentina_recommendation}</p>
            </div>
          )}
        </div>
      )}

      {/* Store analyses */}
      {analyses.length > 0 && (
        <div className="grid md:grid-cols-2 gap-3">
          {analyses.map((a) => (
            <div key={a.store} className="rounded-xl border border-neutral-800/60 bg-neutral-900/50 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white text-sm">{a.store}</h3>
                <span className="text-xs bg-neutral-800 text-neutral-400 px-2 py-0.5 rounded-full">
                  {a.trends.trend_score ?? "?"}/10
                </span>
              </div>
              <p className="text-xs text-neutral-500 leading-relaxed">{a.summary}</p>
              {a.trends.top_products && a.trends.top_products.length > 0 && (
                <div className="space-y-1">
                  {a.trends.top_products.slice(0, 3).map((p, i) => (
                    <p key={i} className="text-xs text-neutral-400">
                      <span className="text-neutral-600 mr-1">{i + 1}.</span>{p}
                    </p>
                  ))}
                </div>
              )}
              {a.trends.colors && a.trends.colors.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {a.trends.colors.slice(0, 3).map((c, i) => (
                    <span key={i} className="text-xs bg-pink-950/60 text-pink-400 px-1.5 py-0.5 rounded-full">{c}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Products */}
      {products.length > 0 && (
        <div className="space-y-4">
          {/* Store filter */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <h2 className="text-sm font-semibold text-neutral-500 uppercase tracking-wide">
              Productos ({storeProducts.length})
            </h2>
            <div className="flex flex-wrap gap-2">
              <StoreBtn active={!selectedStore} onClick={() => { setSelectedStore(null); setActiveSection(""); }}>Todas</StoreBtn>
              {[...new Map(products.map((p) => [p.store_id, p.store])).entries()].map(([sid, sname]) => (
                <StoreBtn key={sid} active={selectedStore === sid} onClick={() => { setSelectedStore(sid === selectedStore ? null : sid); setActiveSection(""); }}>
                  {sname}
                </StoreBtn>
              ))}
            </div>
          </div>

          {/* Section tabs */}
          {availableSections.length > 1 && (
            <div className="flex gap-1 border-b border-neutral-800">
              {availableSections.map(sec => (
                <button key={sec}
                  onClick={() => setActiveSection(sec)}
                  className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
                    currentSection === sec
                      ? "border-white text-white"
                      : "border-transparent text-neutral-500 hover:text-neutral-300"
                  }`}>
                  {SECTION_LABELS[sec] ?? sec}
                  <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                    currentSection === sec ? "bg-neutral-700 text-neutral-300" : "bg-neutral-800 text-neutral-600"
                  }`}>
                    {sectionCounts[sec]}
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* Product grid — 20 per section */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3">
            {sectionProducts.map((p) => (
              <a key={p.id} href={p.product_url ?? "#"} target="_blank" rel="noopener noreferrer"
                className={`group rounded-xl overflow-hidden border bg-neutral-900/50 transition-all ${
                  p.product_url ? "cursor-pointer hover:border-neutral-600 border-neutral-800/60 hover:bg-neutral-900" : "cursor-default border-neutral-800/60"
                }`}>
                <div className="aspect-[3/4] bg-neutral-800 relative overflow-hidden">
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-neutral-700 text-3xl">👗</div>
                  )}
                  <span className={`absolute top-2 left-2 text-xs px-2 py-0.5 rounded-full font-medium backdrop-blur-sm ${
                    p.section === "trending_women" ? "bg-amber-900/80 text-amber-300" : "bg-black/60 text-neutral-300"
                  }`}>
                    {SECTION_LABELS[p.section] ?? p.section}
                  </span>
                  {p.product_url && (
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <span className="flex items-center gap-1.5 bg-white text-neutral-900 text-xs font-semibold px-3 py-1.5 rounded-full">
                        <ExternalLink size={11} /> Ver producto
                      </span>
                    </div>
                  )}
                </div>
                <div className="p-3 space-y-1">
                  <p className="text-xs text-neutral-600">{p.store}</p>
                  <p className="text-sm text-neutral-200 line-clamp-2 leading-snug font-medium">{p.name}</p>
                  {p.price && (
                    <p className="text-sm font-bold text-white pt-0.5">
                      {p.price} <span className="font-normal text-neutral-500">{p.currency}</span>
                    </p>
                  )}
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StoreBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
        active ? "bg-white text-neutral-900" : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700 hover:text-neutral-200"
      }`}>
      {children}
    </button>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "text-emerald-400", running: "text-blue-400",
    failed: "text-red-400", pending: "text-yellow-400",
  };
  return <span className={`font-medium ${styles[status] ?? "text-neutral-400"}`}>{status}</span>;
}

function TagGroup({ title, tags, colorClass }: { title: string; tags?: string[]; colorClass: string }) {
  if (!tags?.length) return null;
  return (
    <div>
      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1.5">{title}</p>
      <div className="flex flex-wrap gap-1">
        {tags.map((t, i) => (
          <span key={i} className={`text-xs px-2 py-0.5 rounded-full font-medium ${colorClass}`}>{t}</span>
        ))}
      </div>
    </div>
  );
}

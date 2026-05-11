"use client";

import { useEffect, useState } from "react";
import { api, Run, TrendAnalysis, Product, Store } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import { ExternalLink } from "lucide-react";

const SECTION_LABELS: Record<string, string> = {
  new_arrivals_women: "Nuevos · Mujer",
  new_arrivals_men:   "Nuevos · Hombre",
  best_sellers_women: "Más vendidos · Mujer",
  best_sellers_men:   "Más vendidos · Hombre",
  new_arrivals:       "Novedades",
  best_sellers:       "Más vendidos",
  trending:           "Trending",
};

const SECTION_FILTERS = [
  { value: "",                    label: "Todo" },
  { value: "new_arrivals_women",  label: "Nuevos · Mujer" },
  { value: "new_arrivals_men",    label: "Nuevos · Hombre" },
  { value: "best_sellers_women",  label: "Más vendidos · Mujer" },
  { value: "best_sellers_men",    label: "Más vendidos · Hombre" },
];

export default function TrendsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStore, setSelectedStore] = useState<number | null>(null);
  const [selectedSection, setSelectedSection] = useState("");
  const [analyses, setAnalyses] = useState<TrendAnalysis[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingData, setLoadingData] = useState(false);

  useEffect(() => {
    Promise.all([api.getRuns(10), api.getStores()]).then(([rs, ss]) => {
      setRuns(rs);
      setStores(ss);
      const completed = rs.find(r => r.status === "completed");
      if (completed) setSelectedRun(completed);
    });
  }, []);

  useEffect(() => {
    if (!selectedRun) return;
    setLoadingData(true);
    Promise.all([
      api.getRunAnalyses(selectedRun.id),
      api.getRunProducts(selectedRun.id, selectedStore ?? undefined),
    ]).then(([a, p]) => { setAnalyses(a); setProducts(p); })
      .finally(() => setLoadingData(false));
  }, [selectedRun, selectedStore]);

  const filteredProducts = selectedSection
    ? products.filter(p => p.section === selectedSection)
    : products;

  const analysis = selectedStore
    ? analyses.find(a => a.store_id === selectedStore)
    : null;

  // Count products per section for the badges
  const sectionCounts = products.reduce((acc, p) => {
    acc[p.section] = (acc[p.section] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Tendencias</h1>
        <p className="text-neutral-500 mt-0.5 text-sm">Productos y análisis de cada tienda.</p>
      </div>

      {/* Run selector */}
      <div className="flex items-center gap-3 flex-wrap">
        <select
          value={selectedRun?.id ?? ""}
          onChange={e => setSelectedRun(runs.find(r => r.id === Number(e.target.value)) ?? null)}
          className="bg-neutral-800 border border-neutral-700/60 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-neutral-500"
        >
          {runs.filter(r => r.status === "completed").map(r => (
            <option key={r.id} value={r.id}>
              {format(new Date(r.run_date), "dd MMM yyyy · HH:mm", { locale: es })}
            </option>
          ))}
        </select>
        {selectedRun && (
          <span className="text-xs text-neutral-600">
            {products.length} productos scrapeados
          </span>
        )}
      </div>

      {/* Store tabs */}
      <div className="flex flex-wrap gap-2">
        <FilterTab active={!selectedStore} onClick={() => setSelectedStore(null)}>Todas las tiendas</FilterTab>
        {stores.map(s => (
          <FilterTab key={s.id} active={selectedStore === s.id} onClick={() => setSelectedStore(selectedStore === s.id ? null : s.id)}>
            {s.name}
          </FilterTab>
        ))}
      </div>

      {/* Section filter */}
      <div className="flex flex-wrap gap-2">
        {SECTION_FILTERS.map(f => (
          <button key={f.value}
            onClick={() => setSelectedSection(selectedSection === f.value ? "" : f.value)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              selectedSection === f.value
                ? "bg-neutral-200 text-neutral-900"
                : "bg-neutral-800/60 text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800"
            }`}
          >
            {f.label}
            {f.value && sectionCounts[f.value] ? (
              <span className={`text-xs rounded-full px-1.5 py-0.5 ${selectedSection === f.value ? "bg-neutral-400 text-neutral-900" : "bg-neutral-700 text-neutral-400"}`}>
                {sectionCounts[f.value]}
              </span>
            ) : null}
          </button>
        ))}
      </div>

      {loadingData ? (
        <div className="text-center py-24 text-neutral-700 text-sm">Cargando...</div>
      ) : (
        <>
          {/* Analysis for selected store */}
          {analysis && <AnalysisCard analysis={analysis} />}

          {/* All analyses grid when no store selected */}
          {!selectedStore && analyses.length > 0 && (
            <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-3">
              {analyses.map(a => (
                <StoreAnalysisMini key={a.store} analysis={a}
                  onClick={() => setSelectedStore(stores.find(s => s.name === a.store)?.id ?? null)} />
              ))}
            </div>
          )}

          {/* Products */}
          {filteredProducts.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-neutral-500 uppercase tracking-wide mb-4">
                Productos ({filteredProducts.length})
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-3">
                {filteredProducts.slice(0, 100).map(p => <ProductCard key={p.id} product={p} />)}
              </div>
            </div>
          )}

          {filteredProducts.length === 0 && !loadingData && selectedRun && (
            <div className="text-center py-20 text-neutral-700 text-sm">
              No hay productos para esta selección.
            </div>
          )}
        </>
      )}
    </div>
  );
}

function FilterTab({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
        active ? "bg-white text-neutral-900" : "bg-neutral-900 border border-neutral-800/60 text-neutral-500 hover:text-neutral-200 hover:border-neutral-700"
      }`}>
      {children}
    </button>
  );
}

function StoreAnalysisMini({ analysis, onClick }: { analysis: TrendAnalysis; onClick: () => void }) {
  return (
    <button onClick={onClick}
      className="text-left rounded-xl border border-neutral-800/60 bg-neutral-900/50 p-4 hover:border-neutral-600 transition-all hover:bg-neutral-900 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-white text-sm">{analysis.store}</h3>
        {analysis.trends.trend_score != null && (
          <span className="text-xs bg-neutral-800 text-neutral-400 px-2 py-0.5 rounded-full">
            {analysis.trends.trend_score}/10
          </span>
        )}
      </div>
      <p className="text-xs text-neutral-500 leading-relaxed line-clamp-2">{analysis.summary}</p>
      {analysis.trends.colors && (
        <div className="flex flex-wrap gap-1">
          {analysis.trends.colors.slice(0, 4).map((c, i) => (
            <span key={i} className="text-xs bg-pink-950/60 text-pink-400 px-1.5 py-0.5 rounded-full">{c}</span>
          ))}
        </div>
      )}
    </button>
  );
}

function AnalysisCard({ analysis }: { analysis: TrendAnalysis }) {
  return (
    <div className="rounded-xl border border-neutral-800/60 bg-neutral-900/50 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-white">{analysis.store}</h2>
        {analysis.trends.trend_score != null && (
          <span className="text-sm bg-neutral-800 text-neutral-300 px-3 py-1 rounded-full">
            Trend score: {analysis.trends.trend_score}/10
          </span>
        )}
      </div>
      <p className="text-neutral-400 text-sm leading-relaxed">{analysis.summary}</p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <PillGroup title="Colores" tags={analysis.trends.colors} cls="bg-pink-950/60 text-pink-400" />
        <PillGroup title="Estilos" tags={analysis.trends.styles} cls="bg-purple-950/60 text-purple-400" />
        <PillGroup title="Categorías" tags={analysis.trends.categories} cls="bg-blue-950/60 text-blue-400" />
        <PillGroup title="Keywords" tags={analysis.trends.keywords} cls="bg-emerald-950/60 text-emerald-400" />
      </div>
      {analysis.trends.price_range?.average && (
        <div className="text-xs text-neutral-600">
          Precio promedio: <span className="text-neutral-400 font-medium">
            {analysis.trends.price_range.min} – {analysis.trends.price_range.max} {analysis.trends.price_range.currency}
          </span>
        </div>
      )}
    </div>
  );
}

function PillGroup({ title, tags, cls }: { title: string; tags?: string[]; cls: string }) {
  if (!tags?.length) return null;
  return (
    <div>
      <p className="text-xs font-semibold text-neutral-600 uppercase tracking-widest mb-2">{title}</p>
      <div className="flex flex-wrap gap-1">
        {tags.map((t, i) => <span key={i} className={`text-xs px-2 py-0.5 rounded-full font-medium ${cls}`}>{t}</span>)}
      </div>
    </div>
  );
}

function ProductCard({ product }: { product: Product }) {
  const sectionLabel = SECTION_LABELS[product.section] ?? product.section;
  const isWomen = product.section.includes("women");
  const isBestSeller = product.section.includes("best_seller");

  return (
    <a href={product.product_url ?? "#"} target="_blank" rel="noopener noreferrer"
      className="group rounded-xl overflow-hidden border border-neutral-800/60 bg-neutral-900/50 hover:border-neutral-600 hover:bg-neutral-900 transition-all">
      <div className="aspect-[3/4] bg-neutral-800 relative overflow-hidden">
        {product.image_url ? (
          <img src={product.image_url} alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-neutral-700 text-3xl">👗</div>
        )}
        <div className="absolute top-2 left-2 flex flex-col gap-1">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium backdrop-blur-sm ${
            isBestSeller ? "bg-amber-900/80 text-amber-300" : "bg-black/60 text-neutral-300"
          }`}>
            {isBestSeller ? "⭐ Best seller" : isWomen ? "Mujer" : "Hombre"}
          </span>
        </div>
        {product.product_url && (
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <span className="flex items-center gap-1.5 bg-white text-neutral-900 text-xs font-semibold px-3 py-1.5 rounded-full">
              <ExternalLink size={11} /> Ver producto
            </span>
          </div>
        )}
      </div>
      <div className="p-3 space-y-1">
        <p className="text-xs text-neutral-600">{product.store}</p>
        <p className="text-sm text-neutral-200 line-clamp-2 leading-snug font-medium">{product.name}</p>
        <div className="flex items-center justify-between pt-0.5">
          {product.price ? (
            <p className="text-sm font-bold text-white">{product.price} <span className="font-normal text-neutral-500">{product.currency}</span></p>
          ) : <span />}
        </div>
      </div>
    </a>
  );
}

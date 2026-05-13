"use client";

import { useEffect, useState } from "react";
import { api, Run, TrendAnalysis, Product, Store, StoreDiff } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import { ExternalLink, TrendingUp, TrendingDown } from "lucide-react";

const SECTION_LABELS: Record<string, string> = {
  new_arrivals_women: "Nuevo · Mujer",
  new_arrivals_men:   "Nuevo · Hombre",
  trending_women:     "Trends · Mujer",
};

const SECTION_ORDER = ["new_arrivals_women", "new_arrivals_men", "trending_women"];

export default function TrendsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStore, setSelectedStore] = useState<number | null>(null);
  const [selectedSection, setSelectedSection] = useState("");
  const [analyses, setAnalyses] = useState<TrendAnalysis[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [diff, setDiff] = useState<StoreDiff[]>([]);
  const [activeTab, setActiveTab] = useState<"products" | "novedades">("products");
  const [activeSection, setActiveSection] = useState<string>("");
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
      api.getRunDiff(selectedRun.id),
    ]).then(([a, p, d]) => { setAnalyses(a); setProducts(p); setDiff(d); })
      .finally(() => setLoadingData(false));
  }, [selectedRun, selectedStore]);

  const analysis = selectedStore
    ? analyses.find(a => a.store_id === selectedStore)
    : null;

  const sectionCounts = products.reduce((acc, p) => {
    acc[p.section] = (acc[p.section] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Sections that actually have products, in display order
  const availableSections = SECTION_ORDER.filter(s => sectionCounts[s] > 0);

  // Auto-select first available section when products load
  const currentSection = activeSection && availableSections.includes(activeSection)
    ? activeSection
    : availableSections[0] ?? "";

  const sectionProducts = currentSection
    ? products.filter(p => p.section === currentSection).slice(0, 20)
    : products.slice(0, 20);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Tendencias</h1>
        <p className="text-neutral-500 mt-0.5 text-sm">Productos y análisis por tienda.</p>
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
          <span className="text-xs text-neutral-600">{products.length} productos</span>
        )}
      </div>

      {/* Store tabs */}
      <div className="flex flex-wrap gap-2">
        <FilterTab active={!selectedStore} onClick={() => setSelectedStore(null)}>Todas</FilterTab>
        {stores.map(s => (
          <FilterTab key={s.id} active={selectedStore === s.id} onClick={() => setSelectedStore(selectedStore === s.id ? null : s.id)}>
            {s.name}
          </FilterTab>
        ))}
      </div>


      {/* Tabs */}
      <div className="flex gap-1 border-b border-neutral-800">
        <TabBtn active={activeTab === "products"} onClick={() => setActiveTab("products")}>
          Productos
        </TabBtn>
        <TabBtn active={activeTab === "novedades"} onClick={() => setActiveTab("novedades")}>
          Novedades vs anterior
          {diff.length > 0 && diff.some(d => d.new_count > 0) && (
            <span className="ml-1.5 bg-emerald-900 text-emerald-400 text-xs px-1.5 py-0.5 rounded-full">
              +{diff.reduce((s, d) => s + d.new_count, 0)}
            </span>
          )}
        </TabBtn>
      </div>

      {loadingData ? (
        <div className="text-center py-24 text-neutral-700 text-sm">Cargando...</div>
      ) : activeTab === "novedades" ? (
        <DiffSection diff={diff} />
      ) : (
        <>
          {/* Analysis for selected store */}
          {analysis && <AnalysisCard analysis={analysis} />}

          {/* All store analyses when no store selected */}
          {!selectedStore && analyses.length > 0 && (
            <div className="grid md:grid-cols-2 gap-3">
              {analyses.map(a => (
                <StoreAnalysisMini key={a.store} analysis={a}
                  onClick={() => setSelectedStore(stores.find(s => s.name === a.store)?.id ?? null)} />
              ))}
            </div>
          )}

          {/* Section tabs */}
          {availableSections.length > 0 && (
            <div className="space-y-4">
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

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3">
                {sectionProducts.map(p => <ProductCard key={p.id} product={p} />)}
              </div>

              {sectionProducts.length === 0 && (
                <div className="text-center py-16 text-neutral-700 text-sm">
                  No hay productos para esta sección.
                </div>
              )}
            </div>
          )}

          {availableSections.length === 0 && !loadingData && selectedRun && (
            <div className="text-center py-20 text-neutral-700 text-sm">
              No hay productos todavía.
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
        active
          ? "bg-white text-neutral-900"
          : "bg-neutral-900 border border-neutral-800/60 text-neutral-500 hover:text-neutral-200 hover:border-neutral-700"
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
      {analysis.trends.top_products && analysis.trends.top_products.length > 0 && (
        <div className="space-y-1">
          {analysis.trends.top_products.slice(0, 3).map((p, i) => (
            <p key={i} className="text-xs text-neutral-400">
              <span className="text-neutral-600 mr-1">{i + 1}.</span>{p}
            </p>
          ))}
        </div>
      )}
      {analysis.trends.colors && (
        <div className="flex flex-wrap gap-1">
          {analysis.trends.colors.slice(0, 3).map((c, i) => (
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
            {analysis.trends.trend_score}/10
          </span>
        )}
      </div>
      <p className="text-neutral-400 text-sm leading-relaxed">{analysis.summary}</p>

      {analysis.trends.top_products && analysis.trends.top_products.length > 0 && (
        <div className="rounded-lg bg-amber-950/20 border border-amber-800/30 p-3 space-y-2">
          <p className="text-xs font-semibold text-amber-500 uppercase tracking-widest">Top productos</p>
          {analysis.trends.top_products.slice(0, 3).map((p, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="text-sm font-bold text-amber-600 w-4">{i + 1}</span>
              <span className="text-sm text-amber-100/80">{p}</span>
            </div>
          ))}
        </div>
      )}

      <div className="grid sm:grid-cols-3 gap-4">
        <PillGroup title="Colores" tags={analysis.trends.colors?.slice(0, 3)} cls="bg-pink-950/60 text-pink-400" />
        <PillGroup title="Estilos" tags={analysis.trends.styles?.slice(0, 3)} cls="bg-purple-950/60 text-purple-400" />
        <PillGroup title="Prendas" tags={analysis.trends.categories?.slice(0, 3)} cls="bg-blue-950/60 text-blue-400" />
      </div>

      {analysis.trends.price_range?.min != null && analysis.trends.price_range?.max != null && (
        <p className="text-xs text-neutral-600">
          Precio: <span className="text-neutral-400 font-medium">
            {analysis.trends.price_range.min} – {analysis.trends.price_range.max} {analysis.trends.price_range.currency}
          </span>
        </p>
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

function TabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center gap-1 ${
        active
          ? "border-white text-white"
          : "border-transparent text-neutral-500 hover:text-neutral-300"
      }`}>
      {children}
    </button>
  );
}

function DiffSection({ diff }: { diff: StoreDiff[] }) {
  if (!diff.length) {
    return (
      <div className="text-center py-20 text-neutral-700 text-sm">
        No hay corrida anterior para comparar.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {diff.map(d => (
        <div key={d.store_id} className="space-y-4">
          {/* Store header */}
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-white">{d.store}</h3>
            <div className="flex items-center gap-3 text-xs text-neutral-600">
              <span>{d.total_prev} → {d.total_current} productos</span>
              <span>vs {format(new Date(d.prev_run_date), "dd MMM", { locale: es })}</span>
            </div>
          </div>

          {/* Summary chips */}
          <div className="flex gap-2 flex-wrap">
            {d.new_count > 0 && (
              <span className="flex items-center gap-1 text-xs bg-emerald-950 text-emerald-400 px-2.5 py-1 rounded-full font-medium">
                <TrendingUp size={11} /> {d.new_count} nuevos
              </span>
            )}
            {d.removed_count > 0 && (
              <span className="flex items-center gap-1 text-xs bg-red-950 text-red-400 px-2.5 py-1 rounded-full font-medium">
                <TrendingDown size={11} /> {d.removed_count} salieron
              </span>
            )}
            {d.new_count === 0 && d.removed_count === 0 && (
              <span className="text-xs text-neutral-600">Sin cambios en esta tienda.</span>
            )}
          </div>

          {/* New products */}
          {d.new_products.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-emerald-500 uppercase tracking-widest mb-3">
                Entraron esta semana
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3">
                {d.new_products.map((p, i) => <ProductCard key={i} product={p} badge="new" />)}
              </div>
            </div>
          )}

          {/* Removed products */}
          {d.removed_products.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-red-500 uppercase tracking-widest mb-3">
                Salieron esta semana
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3">
                {d.removed_products.map((p, i) => <ProductCard key={i} product={p} badge="removed" />)}
              </div>
            </div>
          )}

          {d !== diff[diff.length - 1] && <div className="border-t border-neutral-800/60" />}
        </div>
      ))}
    </div>
  );
}

function ProductCard({ product, badge }: { product: Product; badge?: "new" | "removed" }) {
  const sectionLabel = SECTION_LABELS[product.section] ?? product.section;
  const isTrending = product.section === "trending_women";

  const borderCls = badge === "new"
    ? "border-emerald-800/50 hover:border-emerald-600"
    : badge === "removed"
    ? "border-red-900/40 hover:border-red-700 opacity-70"
    : "border-neutral-800/60 hover:border-neutral-600";

  return (
    <a href={product.product_url ?? "#"} target="_blank" rel="noopener noreferrer"
      className={`group rounded-xl overflow-hidden border bg-neutral-900/50 hover:bg-neutral-900 transition-all ${
        product.product_url ? "cursor-pointer" : "cursor-default"
      } ${borderCls}`}>
      <div className="aspect-[3/4] bg-neutral-800 relative overflow-hidden">
        {product.image_url ? (
          <img src={product.image_url} alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-neutral-700 text-3xl">👗</div>
        )}
        <div className="absolute top-2 left-2 flex flex-col gap-1">
          {badge === "new" && (
            <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-900/90 text-emerald-300 backdrop-blur-sm">
              Nuevo
            </span>
          )}
          {badge === "removed" && (
            <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-red-900/90 text-red-300 backdrop-blur-sm">
              Salió
            </span>
          )}
          {!badge && (
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium backdrop-blur-sm ${
              isTrending ? "bg-amber-900/80 text-amber-300" : "bg-black/60 text-neutral-300"
            }`}>
              {sectionLabel}
            </span>
          )}
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
        {product.price && (
          <p className="text-sm font-bold text-white pt-0.5">
            {product.price} <span className="font-normal text-neutral-500">{product.currency}</span>
          </p>
        )}
      </div>
    </a>
  );
}

"use client";

import { useEffect, useState } from "react";
import { api, Run, TrendAnalysis, Product, Store } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import Image from "next/image";

export default function TrendsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStore, setSelectedStore] = useState<number | null>(null);
  const [analyses, setAnalyses] = useState<TrendAnalysis[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingData, setLoadingData] = useState(false);

  useEffect(() => {
    Promise.all([api.getRuns(10), api.getStores()]).then(([rs, ss]) => {
      setRuns(rs);
      setStores(ss);
      const completed = rs.find((r) => r.status === "completed");
      if (completed) setSelectedRun(completed);
    });
  }, []);

  useEffect(() => {
    if (!selectedRun) return;
    setLoadingData(true);
    Promise.all([
      api.getRunAnalyses(selectedRun.id),
      api.getRunProducts(selectedRun.id, selectedStore ?? undefined),
    ]).then(([a, p]) => {
      setAnalyses(a);
      setProducts(p);
    }).finally(() => setLoadingData(false));
  }, [selectedRun, selectedStore]);

  const filteredAnalysis = selectedStore
    ? analyses.find((a) => a.store_id === selectedStore) ?? null
    : null;

  const displayProducts = products.slice(0, 60);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Tendencias por tienda</h1>
        <p className="text-neutral-400 mt-1">Explorá los productos y análisis de cada corrida.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={selectedRun?.id ?? ""}
          onChange={(e) => {
            const run = runs.find((r) => r.id === Number(e.target.value));
            setSelectedRun(run ?? null);
          }}
          className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-neutral-500"
        >
          {runs.filter((r) => r.status === "completed").map((r) => (
            <option key={r.id} value={r.id}>
              {format(new Date(r.run_date), "dd MMM yyyy", { locale: es })}
            </option>
          ))}
        </select>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedStore(null)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              !selectedStore ? "bg-white text-neutral-900 font-medium" : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700"
            }`}
          >
            Todas
          </button>
          {stores.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedStore(s.id === selectedStore ? null : s.id)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                selectedStore === s.id ? "bg-white text-neutral-900 font-medium" : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700"
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>
      </div>

      {loadingData ? (
        <div className="text-center py-20 text-neutral-500 text-sm">Cargando...</div>
      ) : (
        <>
          {/* Analyses grid */}
          {!selectedStore ? (
            <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
              {analyses.map((a) => (
                <AnalysisCard key={a.store} analysis={a} onClick={() => {
                  const s = stores.find((st) => st.name === a.store);
                  if (s) setSelectedStore(s.id);
                }} />
              ))}
            </div>
          ) : (
            filteredAnalysis && <AnalysisDetail analysis={filteredAnalysis} />
          )}

          {/* Products grid */}
          {displayProducts.length > 0 && (
            <div>
              <h2 className="text-base font-semibold text-white mb-4">
                Productos ({products.length})
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
                {displayProducts.map((p) => (
                  <ProductCard key={p.id} product={p} />
                ))}
              </div>
            </div>
          )}

          {!selectedRun && (
            <div className="text-center py-20 text-neutral-500 text-sm">
              No hay corridas completadas todavía.
            </div>
          )}
        </>
      )}
    </div>
  );
}

function AnalysisCard({ analysis, onClick }: { analysis: TrendAnalysis; onClick: () => void }) {
  const score = analysis.trends.trend_score ?? 0;
  return (
    <button
      onClick={onClick}
      className="text-left rounded-xl border border-neutral-800 bg-neutral-900 p-4 hover:border-neutral-600 transition-colors space-y-3"
    >
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-white">{analysis.store}</h3>
        <span className="text-xs bg-neutral-800 text-neutral-400 px-2 py-0.5 rounded-full">
          Score {score}/10
        </span>
      </div>
      <p className="text-xs text-neutral-400 leading-relaxed line-clamp-3">{analysis.summary}</p>
      {analysis.trends.colors && analysis.trends.colors.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {analysis.trends.colors.slice(0, 4).map((c, i) => (
            <span key={i} className="text-xs bg-pink-950 text-pink-300 px-2 py-0.5 rounded-full">{c}</span>
          ))}
        </div>
      )}
    </button>
  );
}

function AnalysisDetail({ analysis }: { analysis: TrendAnalysis }) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">{analysis.store}</h2>
        <span className="text-sm bg-neutral-800 text-neutral-300 px-3 py-1 rounded-full">
          Trend score: {analysis.trends.trend_score ?? "N/A"}/10
        </span>
      </div>
      <p className="text-neutral-300 text-sm leading-relaxed">{analysis.summary}</p>
      <div className="grid sm:grid-cols-2 gap-4">
        <TagGroup title="Colores" tags={analysis.trends.colors} colorClass="bg-pink-950 text-pink-300" />
        <TagGroup title="Estilos" tags={analysis.trends.styles} colorClass="bg-purple-950 text-purple-300" />
        <TagGroup title="Categorías" tags={analysis.trends.categories} colorClass="bg-blue-950 text-blue-300" />
        <TagGroup title="Keywords" tags={analysis.trends.keywords} colorClass="bg-emerald-950 text-emerald-300" />
      </div>
      {analysis.trends.price_range && (
        <div className="rounded-lg bg-neutral-800 px-4 py-3 text-sm">
          <span className="text-neutral-400">Rango de precio: </span>
          <span className="text-white font-medium">
            {analysis.trends.price_range.min} – {analysis.trends.price_range.max} {analysis.trends.price_range.currency}
          </span>
          {analysis.trends.price_range.average && (
            <span className="text-neutral-400"> (promedio: {analysis.trends.price_range.average})</span>
          )}
        </div>
      )}
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

function ProductCard({ product }: { product: Product }) {
  return (
    <a
      href={product.product_url ?? "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="group rounded-xl overflow-hidden border border-neutral-800 bg-neutral-900 hover:border-neutral-600 transition-colors"
    >
      <div className="aspect-[3/4] bg-neutral-800 relative overflow-hidden">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-neutral-600 text-2xl">👗</div>
        )}
        <span className="absolute top-2 left-2 text-xs bg-black/70 text-neutral-300 px-2 py-0.5 rounded-full">
          {product.section === "new_arrivals" ? "Nuevo" : product.section === "best_sellers" ? "Best seller" : "Trending"}
        </span>
      </div>
      <div className="p-3">
        <p className="text-xs text-neutral-500 mb-0.5">{product.store}</p>
        <p className="text-sm text-neutral-200 line-clamp-2 leading-snug">{product.name}</p>
        <div className="flex items-center justify-between mt-1">
          {product.price ? (
            <p className="text-sm font-medium text-white">{product.price} {product.currency}</p>
          ) : <span />}
          {product.product_url && (
            <span className="text-xs text-neutral-500 group-hover:text-neutral-300 transition-colors">Ver →</span>
          )}
        </div>
      </div>
    </a>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { api, Stats, Run, Store, StoreSection } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import Link from "next/link";
import {
  Play, Settings2, Plus, Trash2, ToggleLeft, ToggleRight,
  ChevronDown, ChevronUp, Save, CheckCircle2, Loader2,
  Globe, ArrowRight, RefreshCw, X, FlaskConical
} from "lucide-react";
import RunConfigModal from "@/components/RunConfigModal";

type UrlTestResult = {
  accessible: boolean;
  estimated_products: number;
  confidence: "alta" | "media" | "baja";
  page_title: string;
  error: string | null;
};

function UrlTestButton({ url }: { url: string }) {
  const [state, setState] = useState<"idle" | "loading" | "done">("idle");
  const [result, setResult] = useState<UrlTestResult | null>(null);

  async function handleTest() {
    if (!url.trim() || state === "loading") return;
    setState("loading");
    setResult(null);
    try {
      const r = await api.testUrl(url.trim());
      setResult(r);
      setState("done");
    } catch {
      setResult({ accessible: false, estimated_products: 0, confidence: "baja", page_title: "", error: "Error al conectar con el servidor" });
      setState("done");
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <button
        onClick={handleTest}
        disabled={!url.trim() || state === "loading"}
        title="Probar si esta URL se puede scrapear"
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-neutral-700 text-xs text-neutral-400 hover:text-white hover:border-neutral-500 transition-colors disabled:opacity-40 whitespace-nowrap"
      >
        {state === "loading"
          ? <Loader2 size={11} className="animate-spin" />
          : <FlaskConical size={11} />}
        {state === "loading" ? "Probando..." : "Probar URL"}
      </button>

      {state === "done" && result && (
        <div className={`text-xs rounded-lg px-2.5 py-1.5 border ${
          result.accessible
            ? result.estimated_products > 5
              ? "bg-emerald-950/40 border-emerald-800/40 text-emerald-300"
              : "bg-yellow-950/40 border-yellow-800/40 text-yellow-300"
            : "bg-red-950/40 border-red-800/40 text-red-300"
        }`}>
          {result.accessible ? (
            <>
              ✅ Accesible · ~<strong>{result.estimated_products}</strong> productos · confianza {result.confidence}
              {result.page_title && <span className="text-xs opacity-60 ml-1">({result.page_title.slice(0, 30)})</span>}
            </>
          ) : (
            <>❌ {result.error || "No accesible"}</>
          )}
        </div>
      )}
    </div>
  );
}

function slugify(str: string) {
  return str.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
}

export default function BackofficePage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [stores, setStores] = useState<Store[]>([]);
  const [triggering, setTriggering] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showConfig, setShowConfig] = useState(false);
  const [showAddStore, setShowAddStore] = useState(false);
  const [expandedStore, setExpandedStore] = useState<number | null>(null);
  const [saving, setSaving] = useState<number | null>(null);
  const [savedId, setSavedId] = useState<number | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // New store form
  const [newName, setNewName] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [newCountry, setNewCountry] = useState("Spain");
  const [newSections, setNewSections] = useState<StoreSection[]>([{ key: "", label: "", url: "" }]);
  const [creating, setCreating] = useState(false);

  const activeRun = runs.find(r => r.status === "running" || r.status === "pending");
  const lastRun = runs[0] ?? null;

  async function loadAll(silent = false) {
    if (!silent) setLoading(true);
    try {
      const [s, ru, st] = await Promise.allSettled([
        api.getStats(), api.getRuns(5), api.getStores(),
      ]);
      if (s.status === "fulfilled") setStats(s.value);
      if (ru.status === "fulfilled") setRuns(ru.value);
      if (st.status === "fulfilled") setStores(st.value);
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => {
    if (activeRun) {
      pollRef.current = setInterval(() => loadAll(true), 3000);
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [activeRun?.id]);

  useEffect(() => { loadAll(); }, []);

  async function handleTrigger(config?: any) {
    setShowConfig(false);
    setTriggering(true);
    try {
      await api.triggerRun(config ?? undefined);
      setTimeout(() => loadAll(true), 2000);
    } catch { } finally { setTriggering(false); }
  }

  async function toggleStore(store: Store) {
    await api.updateStore(store.id, { active: !store.active });
    loadAll(true);
  }

  async function deleteStore(id: number, name: string) {
    if (!confirm(`¿Eliminar "${name}"?`)) return;
    await api.deleteStore(id);
    loadAll(true);
  }

  async function saveStore(store: Store, sections: StoreSection[]) {
    setSaving(store.id);
    try {
      await api.updateStore(store.id, { sections });
      setSavedId(store.id);
      setTimeout(() => setSavedId(null), 2000);
      loadAll(true);
    } finally { setSaving(null); }
  }

  async function createStore() {
    if (!newName.trim() || !newUrl.trim()) return;
    const validSections = newSections.filter(s => s.url.trim()).map(s => ({
      ...s,
      key: s.key.trim() || slugify(s.label || s.url),
      label: s.label.trim() || s.url,
    }));
    setCreating(true);
    try {
      await api.createStore({ name: newName.trim(), url: newUrl.trim(), country: newCountry || "Spain", sections: validSections });
      setNewName(""); setNewUrl(""); setNewCountry("Spain");
      setNewSections([{ key: "", label: "", url: "" }]);
      setShowAddStore(false);
      loadAll(true);
    } finally { setCreating(false); }
  }

  const activeStores = stores.filter(s => s.active);
  const inactiveStores = stores.filter(s => !s.active);

  return (
    <div className="space-y-8">
      {showConfig && <RunConfigModal onClose={() => setShowConfig(false)} onTrigger={handleTrigger} />}

      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-white">Panel de control</h1>
          <p className="text-neutral-500 text-sm mt-0.5">Gestioná tiendas, corridas y resultados</p>
        </div>
        <button onClick={() => loadAll()} disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-neutral-800 text-sm text-neutral-500 hover:text-white transition-colors disabled:opacity-40">
          <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Actualizar
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Tiendas activas", value: stats?.total_stores ?? "—" },
          { label: "Productos totales", value: stats?.total_products?.toLocaleString("es") ?? "—" },
          { label: "Corridas realizadas", value: stats?.total_runs ?? "—" },
          {
            label: "Última corrida",
            value: stats?.last_run_date ? format(new Date(stats.last_run_date), "dd MMM", { locale: es }) : "—",
            sub: stats?.last_run_status,
          },
        ].map(s => (
          <div key={s.label} className="rounded-xl bg-neutral-900 border border-neutral-800/60 px-4 py-3">
            <p className="text-xs text-neutral-600 mb-1">{s.label}</p>
            <p className="text-xl font-bold text-white">{s.value}</p>
            {s.sub && <p className={`text-xs mt-0.5 capitalize ${s.sub === "completed" ? "text-emerald-500" : s.sub === "failed" ? "text-red-500" : "text-neutral-500"}`}>{s.sub}</p>}
          </div>
        ))}
      </div>

      {/* ── CORRIDAS ──────────────────────── */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white uppercase tracking-widest">Corridas de scraping</h2>
          <Link href="/runs" className="text-xs text-neutral-500 hover:text-white flex items-center gap-1 transition-colors">
            Ver historial completo <ArrowRight size={11} />
          </Link>
        </div>

        {/* Run buttons */}
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => handleTrigger(null)} disabled={triggering || !!activeRun}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-neutral-900 text-sm font-semibold hover:bg-neutral-100 transition-colors disabled:opacity-50">
            <Play size={13} fill="currentColor" />
            {triggering ? "Iniciando..." : "Correr todas las tiendas"}
          </button>
          <button onClick={() => setShowConfig(true)} disabled={triggering || !!activeRun}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-neutral-700 text-sm text-neutral-300 hover:text-white hover:border-neutral-500 transition-colors disabled:opacity-50">
            <Settings2 size={13} /> Corrida personalizada
          </button>
        </div>

        {/* Active run */}
        {activeRun && (
          <div className="flex items-center gap-3 bg-blue-950/30 border border-blue-800/30 rounded-xl px-4 py-3">
            <Loader2 size={15} className="animate-spin text-blue-400 shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-blue-200 font-medium">Corrida #{activeRun.id} en progreso</p>
              <p className="text-xs text-blue-400">{activeRun.triggered_by} · Actualizando cada 3 seg...</p>
            </div>
            <Link href={`/runs/${activeRun.id}`}
              className="text-xs text-blue-400 hover:text-blue-200 underline shrink-0">
              Ver detalle →
            </Link>
          </div>
        )}

        {/* Recent runs */}
        {runs.length > 0 && (
          <div className="rounded-xl border border-neutral-800/60 overflow-hidden">
            {runs.slice(0, 4).map((run, i) => (
              <Link key={run.id} href={`/runs/${run.id}`}
                className={`flex items-center gap-3 px-4 py-3 hover:bg-white/3 transition-colors ${i > 0 ? "border-t border-neutral-800/40" : ""}`}>
                <div className={`w-2 h-2 rounded-full shrink-0 ${
                  run.status === "completed" ? "bg-emerald-500" :
                  run.status === "running" ? "bg-blue-400 animate-pulse" :
                  run.status === "failed" ? "bg-red-500" : "bg-yellow-500"
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-neutral-200 truncate">Corrida #{run.id}</p>
                  <p className="text-xs text-neutral-600 truncate">{run.triggered_by}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs text-neutral-500">
                    {format(new Date(run.run_date), "dd MMM · HH:mm", { locale: es })}
                  </p>
                  <p className={`text-xs capitalize font-medium ${
                    run.status === "completed" ? "text-emerald-500" :
                    run.status === "running" ? "text-blue-400" :
                    run.status === "failed" ? "text-red-400" : "text-yellow-400"
                  }`}>{run.status}</p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* ── TIENDAS ──────────────────────── */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white uppercase tracking-widest">Tiendas</h2>
          <button onClick={() => setShowAddStore(!showAddStore)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white text-neutral-900 text-xs font-semibold hover:bg-neutral-100 transition-colors">
            <Plus size={12} /> Agregar tienda
          </button>
        </div>

        {/* Add store form */}
        {showAddStore && (
          <div className="rounded-xl border border-neutral-700/60 bg-neutral-900/60 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-white">Nueva tienda</p>
              <button onClick={() => setShowAddStore(false)} className="text-neutral-600 hover:text-white transition-colors">
                <X size={14} />
              </button>
            </div>
            <div className="grid sm:grid-cols-3 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-neutral-500">Nombre *</label>
                <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="ej: Springfield"
                  className="w-full bg-neutral-800 border border-neutral-700 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500" />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-neutral-500">URL principal *</label>
                <input value={newUrl} onChange={e => setNewUrl(e.target.value)} placeholder="https://www.tienda.com/es/"
                  className="w-full bg-neutral-800 border border-neutral-700 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500" />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-neutral-500">País</label>
                <input value={newCountry} onChange={e => setNewCountry(e.target.value)} placeholder="Spain"
                  className="w-full bg-neutral-800 border border-neutral-700 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500" />
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-xs text-neutral-500 font-semibold uppercase tracking-widest">Secciones a scrapear</p>
              {newSections.map((sec, i) => (
                <div key={i} className="space-y-1.5">
                  <div className="grid grid-cols-[1.5fr_2fr_auto] gap-2 items-center">
                    <input value={sec.label} onChange={e => {
                      const s = [...newSections]; s[i] = { ...s[i], label: e.target.value, key: slugify(e.target.value) }; setNewSections(s);
                    }} placeholder="Nombre (ej: Nuevo · Mujer)"
                      className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500" />
                    <input value={sec.url} onChange={e => {
                      const s = [...newSections]; s[i] = { ...s[i], url: e.target.value }; setNewSections(s);
                    }} placeholder="URL de la sección *"
                      className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500" />
                    <button onClick={() => setNewSections(newSections.filter((_, j) => j !== i))}
                      className="text-neutral-600 hover:text-red-400 transition-colors p-1">
                      <Trash2 size={13} />
                    </button>
                  </div>
                  {sec.url.startsWith("http") && <UrlTestButton url={sec.url} />}
                </div>
              ))}
              <button onClick={() => setNewSections([...newSections, { key: "", label: "", url: "" }])}
                className="text-xs text-neutral-500 hover:text-white flex items-center gap-1 transition-colors">
                <Plus size={11} /> Agregar sección
              </button>
            </div>

            <div className="flex gap-2 pt-1">
              <button onClick={createStore} disabled={!newName.trim() || !newUrl.trim() || creating}
                className="px-4 py-2 rounded-lg bg-white text-neutral-900 text-sm font-semibold hover:bg-neutral-100 transition-colors disabled:opacity-40">
                {creating ? "Creando..." : "Crear tienda"}
              </button>
              <button onClick={() => setShowAddStore(false)}
                className="px-4 py-2 rounded-lg bg-neutral-800 text-neutral-400 text-sm hover:text-white transition-colors">
                Cancelar
              </button>
            </div>
          </div>
        )}

        {/* Active stores */}
        {stores.length === 0 && !showAddStore ? (
          <div className="text-center py-12 rounded-xl border border-dashed border-neutral-800">
            <Globe size={24} className="mx-auto text-neutral-700 mb-2" />
            <p className="text-neutral-600 text-sm">No hay tiendas. Agregá la primera.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {activeStores.map(store => (
              <StoreRow key={store.id} store={store}
                expanded={expandedStore === store.id}
                onToggleExpand={() => setExpandedStore(expandedStore === store.id ? null : store.id)}
                onToggleActive={() => toggleStore(store)}
                onDelete={() => deleteStore(store.id, store.name)}
                onSave={sections => saveStore(store, sections)}
                saving={saving === store.id} saved={savedId === store.id}
              />
            ))}
            {inactiveStores.length > 0 && (
              <>
                <p className="text-xs text-neutral-600 uppercase tracking-widest px-1 pt-2">Inactivas</p>
                {inactiveStores.map(store => (
                  <StoreRow key={store.id} store={store}
                    expanded={expandedStore === store.id}
                    onToggleExpand={() => setExpandedStore(expandedStore === store.id ? null : store.id)}
                    onToggleActive={() => toggleStore(store)}
                    onDelete={() => deleteStore(store.id, store.name)}
                    onSave={sections => saveStore(store, sections)}
                    saving={saving === store.id} saved={savedId === store.id}
                  />
                ))}
              </>
            )}
          </div>
        )}
      </section>

      {/* ── ACCESOS RÁPIDOS ──────────────────────── */}
      <section className="grid sm:grid-cols-3 gap-3">
        {[
          { href: "/trends",   label: "Ver productos",     desc: "Grilla de productos scrapeados" },
          { href: "/analysis", label: "Ver análisis",      desc: "Tendencias por tienda" },
          { href: "/runs",     label: "Historial completo",desc: "Todas las corridas y resultados" },
        ].map(l => (
          <Link key={l.href} href={l.href}
            className="rounded-xl border border-neutral-800/60 bg-neutral-900/40 px-4 py-4 hover:border-neutral-700 hover:bg-neutral-900 transition-all group">
            <p className="text-sm font-semibold text-white group-hover:text-white">{l.label}</p>
            <p className="text-xs text-neutral-600 mt-0.5">{l.desc}</p>
            <ArrowRight size={13} className="text-neutral-700 group-hover:text-neutral-400 mt-3 transition-colors" />
          </Link>
        ))}
      </section>

    </div>
  );
}

function StoreRow({ store, expanded, onToggleExpand, onToggleActive, onDelete, onSave, saving, saved }: {
  store: Store; expanded: boolean;
  onToggleExpand: () => void; onToggleActive: () => void; onDelete: () => void;
  onSave: (s: StoreSection[]) => void; saving: boolean; saved: boolean;
}) {
  const [sections, setSections] = useState<StoreSection[]>(store.sections || []);
  useEffect(() => { setSections(store.sections || []); }, [store.sections]);

  return (
    <div className={`rounded-xl border transition-colors ${store.active ? "border-neutral-800/60 bg-neutral-900/40" : "border-neutral-800/30 bg-neutral-900/20 opacity-55"}`}>
      <div className="flex items-center gap-3 px-4 py-3">
        <div className={`w-2 h-2 rounded-full shrink-0 ${store.active ? "bg-emerald-500" : "bg-neutral-600"}`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white truncate">{store.name}</p>
          <p className="text-xs text-neutral-600">{store.country} · {store.sections?.length || 0} sección{store.sections?.length !== 1 ? "es" : ""}</p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button onClick={onToggleActive} title={store.active ? "Desactivar" : "Activar"}
            className="p-1.5 text-neutral-500 hover:text-white transition-colors">
            {store.active ? <ToggleRight size={18} className="text-emerald-500" /> : <ToggleLeft size={18} />}
          </button>
          <button onClick={onDelete} className="p-1.5 text-neutral-600 hover:text-red-400 transition-colors">
            <Trash2 size={14} />
          </button>
          <button onClick={onToggleExpand} className="p-1.5 text-neutral-600 hover:text-white transition-colors">
            {expanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-neutral-800/60 px-4 py-4 space-y-3">
          <p className="text-xs font-semibold text-neutral-500 uppercase tracking-widest">Secciones</p>
          {sections.length === 0 && (
            <p className="text-xs text-neutral-600 italic">Sin secciones — esta tienda no se scrapeará.</p>
          )}
          {sections.map((sec, i) => (
            <div key={i} className="space-y-1.5">
              <div className="grid grid-cols-[1.5fr_2fr_auto] gap-2 items-center">
                <input value={sec.label} onChange={e => { const s = [...sections]; s[i] = { ...s[i], label: e.target.value }; setSections(s); }}
                  placeholder="Nombre visible"
                  className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-neutral-500" />
                <input value={sec.url} onChange={e => { const s = [...sections]; s[i] = { ...s[i], url: e.target.value }; setSections(s); }}
                  placeholder="URL de la sección"
                  className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-neutral-500" />
                <button onClick={() => setSections(sections.filter((_, j) => j !== i))}
                  className="text-neutral-600 hover:text-red-400 transition-colors p-1">
                  <Trash2 size={13} />
                </button>
              </div>
              {sec.url.startsWith("http") && <UrlTestButton url={sec.url} />}
            </div>
          ))}
          <button onClick={() => setSections([...sections, { key: slugify(String(Date.now())), label: "", url: "" }])}
            className="text-xs text-neutral-500 hover:text-white flex items-center gap-1 transition-colors">
            <Plus size={11} /> Agregar sección
          </button>
          <button onClick={() => onSave(sections)} disabled={saving}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${saved ? "bg-emerald-900/60 text-emerald-300 border border-emerald-700/40" : "bg-neutral-700 hover:bg-neutral-600 text-white"} disabled:opacity-50`}>
            {saved ? <><CheckCircle2 size={12} /> Guardado</> : <><Save size={12} /> {saving ? "Guardando..." : "Guardar cambios"}</>}
          </button>
        </div>
      )}
    </div>
  );
}

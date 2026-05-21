"use client";

import { useEffect, useState } from "react";
import { api, Store, StoreSection } from "@/lib/api";
import {
  Plus, Trash2, ToggleLeft, ToggleRight,
  ChevronDown, ChevronUp, Save, CheckCircle2, Globe
} from "lucide-react";

function slugify(str: string) {
  return str
    .toLowerCase()
    .normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
}

export default function StoresPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [saving, setSaving] = useState<number | null>(null);
  const [savedId, setSavedId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  // New store form
  const [newName, setNewName] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [newCountry, setNewCountry] = useState("Spain");
  const [newSections, setNewSections] = useState<StoreSection[]>([
    { key: "", label: "", url: "" }
  ]);

  useEffect(() => { loadStores(); }, []);

  async function loadStores() {
    setLoading(true);
    try { setStores(await api.getStores()); }
    finally { setLoading(false); }
  }

  async function toggleActive(store: Store) {
    await api.updateStore(store.id, { active: !store.active });
    loadStores();
  }

  async function deleteStore(id: number, name: string) {
    if (!confirm(`¿Eliminar "${name}"? Esta acción no se puede deshacer.`)) return;
    await api.deleteStore(id);
    loadStores();
  }

  async function saveStore(store: Store, sections: StoreSection[]) {
    setSaving(store.id);
    try {
      await api.updateStore(store.id, { sections });
      setSavedId(store.id);
      setTimeout(() => setSavedId(null), 2000);
      loadStores();
    } finally { setSaving(null); }
  }

  async function createStore() {
    if (!newName.trim() || !newUrl.trim()) return;
    const validSections = newSections
      .filter(s => s.url.trim())
      .map(s => ({
        ...s,
        key: s.key.trim() || slugify(s.label || s.url),
        label: s.label.trim() || s.url,
      }));
    setCreating(true);
    try {
      await api.createStore({
        name: newName.trim(),
        url: newUrl.trim(),
        country: newCountry.trim() || "Spain",
        sections: validSections,
      });
      setNewName(""); setNewUrl(""); setNewCountry("Spain");
      setNewSections([{ key: "", label: "", url: "" }]);
      setShowAdd(false);
      loadStores();
    } finally { setCreating(false); }
  }

  const activeStores = stores.filter(s => s.active);
  const inactiveStores = stores.filter(s => !s.active);

  if (loading) return <div className="text-center py-20 text-neutral-700 text-sm">Cargando...</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Tiendas</h1>
          <p className="text-neutral-600 text-sm mt-0.5">
            {activeStores.length} activa{activeStores.length !== 1 ? "s" : ""} · {stores.length} en total
          </p>
        </div>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white text-neutral-900 text-sm font-semibold hover:bg-neutral-100 transition-colors"
        >
          <Plus size={13} /> Agregar tienda
        </button>
      </div>

      {/* Add store form */}
      {showAdd && (
        <div className="rounded-xl border border-neutral-700/60 bg-neutral-900/60 p-5 space-y-4">
          <p className="text-sm font-semibold text-white">Nueva tienda</p>

          <div className="grid sm:grid-cols-3 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-neutral-500">Nombre *</label>
              <input
                value={newName}
                onChange={e => setNewName(e.target.value)}
                placeholder="ej: Springfield"
                className="w-full bg-neutral-800 border border-neutral-700 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-neutral-500">URL principal *</label>
              <input
                value={newUrl}
                onChange={e => setNewUrl(e.target.value)}
                placeholder="ej: https://www.springfield.com/es/"
                className="w-full bg-neutral-800 border border-neutral-700 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-neutral-500">País</label>
              <input
                value={newCountry}
                onChange={e => setNewCountry(e.target.value)}
                placeholder="ej: Spain"
                className="w-full bg-neutral-800 border border-neutral-700 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500"
              />
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold text-neutral-500 uppercase tracking-widest">
              Secciones a scrapear
            </p>
            <p className="text-xs text-neutral-600">
              Cada sección es una URL que se va a scrapear. El nombre visible aparece en los resultados.
            </p>
            {newSections.map((sec, i) => (
              <div key={i} className="grid grid-cols-[1.5fr_1.5fr_2fr_auto] gap-2 items-center">
                <input
                  value={sec.label}
                  onChange={e => {
                    const s = [...newSections];
                    s[i] = { ...s[i], label: e.target.value, key: slugify(e.target.value) };
                    setNewSections(s);
                  }}
                  placeholder="Nombre (ej: Nuevo · Mujer)"
                  className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500"
                />
                <input
                  value={sec.key}
                  onChange={e => {
                    const s = [...newSections];
                    s[i] = { ...s[i], key: e.target.value };
                    setNewSections(s);
                  }}
                  placeholder="ID interno (auto)"
                  className="bg-neutral-800 border border-neutral-700/50 text-neutral-500 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500 focus:text-neutral-200"
                />
                <input
                  value={sec.url}
                  onChange={e => {
                    const s = [...newSections];
                    s[i] = { ...s[i], url: e.target.value };
                    setNewSections(s);
                  }}
                  placeholder="URL de la sección *"
                  className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500"
                />
                <button
                  onClick={() => setNewSections(newSections.filter((_, j) => j !== i))}
                  className="text-neutral-600 hover:text-red-400 transition-colors p-1"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
            <button
              onClick={() => setNewSections([...newSections, { key: "", label: "", url: "" }])}
              className="text-xs text-neutral-500 hover:text-white flex items-center gap-1 transition-colors"
            >
              <Plus size={11} /> Agregar sección
            </button>
          </div>

          <div className="flex gap-2 pt-1">
            <button
              onClick={createStore}
              disabled={!newName.trim() || !newUrl.trim() || creating}
              className="px-4 py-1.5 rounded-lg bg-white text-neutral-900 text-sm font-semibold hover:bg-neutral-100 transition-colors disabled:opacity-40"
            >
              {creating ? "Creando..." : "Crear tienda"}
            </button>
            <button
              onClick={() => setShowAdd(false)}
              className="px-4 py-1.5 rounded-lg bg-neutral-800 text-neutral-400 text-sm hover:text-white transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Active stores */}
      {activeStores.length > 0 && (
        <div className="space-y-3">
          {activeStores.map(store => (
            <StoreCard
              key={store.id}
              store={store}
              expanded={expanded === store.id}
              onToggleExpand={() => setExpanded(expanded === store.id ? null : store.id)}
              onToggleActive={() => toggleActive(store)}
              onDelete={() => deleteStore(store.id, store.name)}
              onSave={(sections) => saveStore(store, sections)}
              saving={saving === store.id}
              saved={savedId === store.id}
            />
          ))}
        </div>
      )}

      {/* Inactive stores */}
      {inactiveStores.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-neutral-600 uppercase tracking-widest px-1">Inactivas</p>
          {inactiveStores.map(store => (
            <StoreCard
              key={store.id}
              store={store}
              expanded={expanded === store.id}
              onToggleExpand={() => setExpanded(expanded === store.id ? null : store.id)}
              onToggleActive={() => toggleActive(store)}
              onDelete={() => deleteStore(store.id, store.name)}
              onSave={(sections) => saveStore(store, sections)}
              saving={saving === store.id}
              saved={savedId === store.id}
            />
          ))}
        </div>
      )}

      {stores.length === 0 && !showAdd && (
        <div className="text-center py-16 text-neutral-600 text-sm space-y-2">
          <Globe size={28} className="mx-auto text-neutral-700" />
          <p>No hay tiendas configuradas.</p>
          <button onClick={() => setShowAdd(true)} className="text-white underline text-xs">
            Agregar la primera
          </button>
        </div>
      )}
    </div>
  );
}

function StoreCard({
  store, expanded, onToggleExpand, onToggleActive, onDelete, onSave, saving, saved
}: {
  store: Store;
  expanded: boolean;
  onToggleExpand: () => void;
  onToggleActive: () => void;
  onDelete: () => void;
  onSave: (sections: StoreSection[]) => void;
  saving: boolean;
  saved: boolean;
}) {
  const [sections, setSections] = useState<StoreSection[]>(store.sections || []);

  useEffect(() => { setSections(store.sections || []); }, [store.sections]);

  return (
    <div className={`rounded-xl border transition-colors ${
      store.active
        ? "border-neutral-800/60 bg-neutral-900/50"
        : "border-neutral-800/30 bg-neutral-900/20 opacity-55"
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className={`w-2 h-2 rounded-full shrink-0 ${store.active ? "bg-emerald-500" : "bg-neutral-600"}`} />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white truncate">{store.name}</p>
            <p className="text-xs text-neutral-600">
              {store.country} · {store.sections?.length || 0} sección{(store.sections?.length || 0) !== 1 ? "es" : ""}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0 ml-3">
          <button
            onClick={onToggleActive}
            className="text-neutral-500 hover:text-white transition-colors p-1"
            title={store.active ? "Desactivar" : "Activar"}
          >
            {store.active
              ? <ToggleRight size={18} className="text-emerald-500" />
              : <ToggleLeft size={18} />}
          </button>
          <button onClick={onDelete} className="text-neutral-600 hover:text-red-400 transition-colors p-1">
            <Trash2 size={14} />
          </button>
          <button onClick={onToggleExpand} className="text-neutral-600 hover:text-white transition-colors p-1">
            {expanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
          </button>
        </div>
      </div>

      {/* Sections editor */}
      {expanded && (
        <div className="border-t border-neutral-800/60 px-4 py-4 space-y-3">
          <p className="text-xs font-semibold text-neutral-500 uppercase tracking-widest">Secciones</p>

          {sections.length === 0 && (
            <p className="text-xs text-neutral-600 italic">Sin secciones. Esta tienda no se scrapeará.</p>
          )}

          {sections.map((sec, i) => (
            <div key={i} className="grid grid-cols-[1.5fr_1.5fr_2fr_auto] gap-2 items-center">
              <input
                value={sec.label}
                onChange={e => {
                  const s = [...sections]; s[i] = { ...s[i], label: e.target.value }; setSections(s);
                }}
                placeholder="Nombre visible"
                className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-neutral-500"
              />
              <input
                value={sec.key}
                onChange={e => {
                  const s = [...sections]; s[i] = { ...s[i], key: e.target.value }; setSections(s);
                }}
                placeholder="ID interno"
                className="bg-neutral-800 border border-neutral-700/50 text-neutral-500 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-neutral-500 focus:text-neutral-200"
              />
              <input
                value={sec.url}
                onChange={e => {
                  const s = [...sections]; s[i] = { ...s[i], url: e.target.value }; setSections(s);
                }}
                placeholder="URL de la sección"
                className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-neutral-500"
              />
              <button
                onClick={() => setSections(sections.filter((_, j) => j !== i))}
                className="text-neutral-600 hover:text-red-400 transition-colors p-1"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}

          <button
            onClick={() => setSections([...sections, { key: "", label: "", url: "" }])}
            className="text-xs text-neutral-500 hover:text-white flex items-center gap-1 transition-colors"
          >
            <Plus size={11} /> Agregar sección
          </button>

          <button
            onClick={() => onSave(sections)}
            disabled={saving}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              saved
                ? "bg-emerald-900/60 text-emerald-300 border border-emerald-700/40"
                : "bg-neutral-700 hover:bg-neutral-600 text-white"
            } disabled:opacity-50`}
          >
            {saved
              ? <><CheckCircle2 size={12} /> Guardado</>
              : <><Save size={12} /> {saving ? "Guardando..." : "Guardar cambios"}</>
            }
          </button>
        </div>
      )}
    </div>
  );
}

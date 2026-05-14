"use client";

import { useEffect, useState } from "react";
import { api, Store, StoreSection } from "@/lib/api";
import { Plus, Trash2, ToggleLeft, ToggleRight, ChevronDown, ChevronUp, Save } from "lucide-react";

export default function StoresPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [saving, setSaving] = useState<number | null>(null);

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
    try {
      setStores(await api.getStores());
    } finally { setLoading(false); }
  }

  async function toggleActive(store: Store) {
    await api.updateStore(store.id, { active: !store.active });
    loadStores();
  }

  async function deleteStore(id: number) {
    if (!confirm("¿Eliminar esta tienda?")) return;
    await api.deleteStore(id);
    loadStores();
  }

  async function saveStore(store: Store, sections: StoreSection[]) {
    setSaving(store.id);
    try {
      await api.updateStore(store.id, { sections });
      loadStores();
    } finally { setSaving(null); }
  }

  async function createStore() {
    if (!newName || !newUrl) return;
    const validSections = newSections.filter(s => s.key && s.url);
    await api.createStore({ name: newName, url: newUrl, country: newCountry, sections: validSections });
    setNewName(""); setNewUrl(""); setNewCountry("Spain");
    setNewSections([{ key: "", label: "", url: "" }]);
    setShowAdd(false);
    loadStores();
  }

  if (loading) return <div className="text-center py-20 text-neutral-700 text-sm">Cargando...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Tiendas</h1>
          <p className="text-neutral-600 text-sm mt-0.5">Gestioná las tiendas y sus secciones a scrapear</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white text-neutral-900 text-sm font-semibold hover:bg-neutral-100 transition-colors">
          <Plus size={13} /> Agregar tienda
        </button>
      </div>

      {/* Add store form */}
      {showAdd && (
        <div className="rounded-xl border border-neutral-700/60 bg-neutral-900/60 p-5 space-y-4">
          <p className="text-sm font-semibold text-white">Nueva tienda</p>
          <div className="grid sm:grid-cols-3 gap-3">
            <input value={newName} onChange={e => setNewName(e.target.value)}
              placeholder="Nombre (ej: Mango)"
              className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500" />
            <input value={newUrl} onChange={e => setNewUrl(e.target.value)}
              placeholder="URL principal (ej: https://shop.mango.com/es/)"
              className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500" />
            <input value={newCountry} onChange={e => setNewCountry(e.target.value)}
              placeholder="País (ej: Spain)"
              className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-neutral-500" />
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold text-neutral-500 uppercase tracking-widest">Secciones a scrapear</p>
            {newSections.map((sec, i) => (
              <div key={i} className="grid grid-cols-[1fr_1fr_2fr_auto] gap-2">
                <input value={sec.key} onChange={e => {
                  const s = [...newSections]; s[i] = { ...s[i], key: e.target.value }; setNewSections(s);
                }} placeholder="Key (ej: new_women)"
                  className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none" />
                <input value={sec.label} onChange={e => {
                  const s = [...newSections]; s[i] = { ...s[i], label: e.target.value }; setNewSections(s);
                }} placeholder="Label (ej: Nuevo · Mujer)"
                  className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none" />
                <input value={sec.url} onChange={e => {
                  const s = [...newSections]; s[i] = { ...s[i], url: e.target.value }; setNewSections(s);
                }} placeholder="URL de la sección"
                  className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none" />
                <button onClick={() => setNewSections(newSections.filter((_, j) => j !== i))}
                  className="text-neutral-600 hover:text-red-400 transition-colors">
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
            <button onClick={() => setNewSections([...newSections, { key: "", label: "", url: "" }])}
              className="text-xs text-neutral-500 hover:text-white flex items-center gap-1 transition-colors">
              <Plus size={11} /> Agregar sección
            </button>
          </div>

          <div className="flex gap-2">
            <button onClick={createStore}
              className="px-4 py-1.5 rounded-lg bg-white text-neutral-900 text-sm font-semibold hover:bg-neutral-100 transition-colors">
              Crear tienda
            </button>
            <button onClick={() => setShowAdd(false)}
              className="px-4 py-1.5 rounded-lg bg-neutral-800 text-neutral-400 text-sm hover:text-white transition-colors">
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Store list */}
      <div className="space-y-3">
        {stores.map(store => (
          <StoreCard
            key={store.id}
            store={store}
            expanded={expanded === store.id}
            onToggleExpand={() => setExpanded(expanded === store.id ? null : store.id)}
            onToggleActive={() => toggleActive(store)}
            onDelete={() => deleteStore(store.id)}
            onSave={(sections) => saveStore(store, sections)}
            saving={saving === store.id}
          />
        ))}
      </div>
    </div>
  );
}

function StoreCard({
  store, expanded, onToggleExpand, onToggleActive, onDelete, onSave, saving
}: {
  store: Store;
  expanded: boolean;
  onToggleExpand: () => void;
  onToggleActive: () => void;
  onDelete: () => void;
  onSave: (sections: StoreSection[]) => void;
  saving: boolean;
}) {
  const [sections, setSections] = useState<StoreSection[]>(store.sections || []);

  useEffect(() => { setSections(store.sections || []); }, [store.sections]);

  return (
    <div className={`rounded-xl border transition-colors ${store.active ? "border-neutral-800/60 bg-neutral-900/50" : "border-neutral-800/30 bg-neutral-900/20 opacity-60"}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${store.active ? "bg-emerald-500" : "bg-neutral-600"}`} />
          <div>
            <p className="text-sm font-semibold text-white">{store.name}</p>
            <p className="text-xs text-neutral-600">{store.country} · {store.sections?.length || 0} secciones</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onToggleActive} className="text-neutral-500 hover:text-white transition-colors" title={store.active ? "Desactivar" : "Activar"}>
            {store.active ? <ToggleRight size={18} className="text-emerald-500" /> : <ToggleLeft size={18} />}
          </button>
          <button onClick={onDelete} className="text-neutral-600 hover:text-red-400 transition-colors">
            <Trash2 size={14} />
          </button>
          <button onClick={onToggleExpand} className="text-neutral-600 hover:text-white transition-colors">
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {/* Sections editor */}
      {expanded && (
        <div className="border-t border-neutral-800/60 px-4 py-4 space-y-3">
          <p className="text-xs font-semibold text-neutral-500 uppercase tracking-widest">Secciones</p>

          {sections.map((sec, i) => (
            <div key={i} className="grid grid-cols-[1fr_1fr_2fr_auto] gap-2">
              <input value={sec.key} onChange={e => {
                const s = [...sections]; s[i] = { ...s[i], key: e.target.value }; setSections(s);
              }} placeholder="Key"
                className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none" />
              <input value={sec.label} onChange={e => {
                const s = [...sections]; s[i] = { ...s[i], label: e.target.value }; setSections(s);
              }} placeholder="Label"
                className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none" />
              <input value={sec.url} onChange={e => {
                const s = [...sections]; s[i] = { ...s[i], url: e.target.value }; setSections(s);
              }} placeholder="URL"
                className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none" />
              <button onClick={() => setSections(sections.filter((_, j) => j !== i))}
                className="text-neutral-600 hover:text-red-400 transition-colors">
                <Trash2 size={14} />
              </button>
            </div>
          ))}

          <button onClick={() => setSections([...sections, { key: "", label: "", url: "" }])}
            className="text-xs text-neutral-500 hover:text-white flex items-center gap-1 transition-colors">
            <Plus size={11} /> Agregar sección
          </button>

          <button onClick={() => onSave(sections)} disabled={saving}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neutral-700 hover:bg-neutral-600 text-white text-xs font-medium transition-colors disabled:opacity-50">
            <Save size={12} /> {saving ? "Guardando..." : "Guardar cambios"}
          </button>
        </div>
      )}
    </div>
  );
}

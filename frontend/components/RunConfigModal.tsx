"use client";

import { useEffect, useState } from "react";
import { api, Section, Store } from "@/lib/api";
import { X, Play, CheckSquare, Square, ChevronDown, ChevronRight } from "lucide-react";

interface StoreConfig {
  store: string;
  sections: Section[];
}

interface Props {
  onClose: () => void;
  onTrigger: (config: StoreConfig[] | null) => void;
}

export default function RunConfigModal({ onClose, onTrigger }: Props) {
  const [registry, setRegistry] = useState<{ store: string; sections: Section[] }[]>([]);
  const [selected, setSelected] = useState<Record<string, Set<string>>>({});
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [mode, setMode] = useState<"all" | "custom">("all");

  useEffect(() => {
    // Use DB stores (includes stores added via UI), filter active only
    api.getStores().then(stores => {
      const active = stores.filter(s => s.active && s.sections?.length > 0);
      const data = active.map(s => ({ store: s.name, sections: s.sections as Section[] }));
      setRegistry(data);
      const initial: Record<string, Set<string>> = {};
      data.forEach(({ store, sections }) => {
        initial[store] = new Set(sections.map(s => s.key));
      });
      setSelected(initial);
      setExpanded(Object.fromEntries(data.map(d => [d.store, true])));
    });
  }, []);

  function toggleSection(store: string, key: string) {
    setSelected(prev => {
      const next = { ...prev, [store]: new Set(prev[store]) };
      if (next[store].has(key)) next[store].delete(key);
      else next[store].add(key);
      return next;
    });
  }

  function toggleStore(store: string, sections: Section[]) {
    setSelected(prev => {
      const allSelected = sections.every(s => prev[store]?.has(s.key));
      return {
        ...prev,
        [store]: allSelected ? new Set() : new Set(sections.map(s => s.key)),
      };
    });
  }

  function handleRun() {
    if (mode === "all") { onTrigger(null); return; }

    const config: StoreConfig[] = [];
    for (const { store, sections } of registry) {
      const selectedSections = sections.filter(s => selected[store]?.has(s.key));
      if (selectedSections.length > 0) {
        config.push({ store, sections: selectedSections });
      }
    }
    if (config.length === 0) return;
    onTrigger(config);
  }

  const totalSelected = Object.values(selected).reduce((n, s) => n + s.size, 0);

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-neutral-900 border border-neutral-800 rounded-2xl w-full max-w-lg max-h-[85vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-neutral-800">
          <div>
            <h2 className="text-base font-bold text-white">Configurar corrida</h2>
            <p className="text-xs text-neutral-500 mt-0.5">Elegí qué tiendas y secciones scrapear</p>
          </div>
          <button onClick={onClose} className="text-neutral-600 hover:text-white transition-colors p-1">
            <X size={18} />
          </button>
        </div>

        {/* Mode toggle */}
        <div className="px-5 py-3 border-b border-neutral-800 flex gap-2">
          <ModeBtn active={mode === "all"} onClick={() => setMode("all")}>Todo (completo)</ModeBtn>
          <ModeBtn active={mode === "custom"} onClick={() => setMode("custom")}>Personalizado</ModeBtn>
        </div>

        {/* Store list */}
        {mode === "custom" && (
          <div className="overflow-y-auto flex-1 px-5 py-3 space-y-2">
            {registry.map(({ store, sections }) => {
              const storeSelected = sections.filter(s => selected[store]?.has(s.key));
              const allOn = storeSelected.length === sections.length;
              const someOn = storeSelected.length > 0 && !allOn;
              const isExpanded = expanded[store];

              return (
                <div key={store} className="rounded-xl border border-neutral-800/60 overflow-hidden">
                  {/* Store header */}
                  <div className="flex items-center gap-3 px-4 py-3 bg-neutral-800/30">
                    <button onClick={() => toggleStore(store, sections)} className="text-neutral-400 hover:text-white transition-colors">
                      {allOn ? <CheckSquare size={15} className="text-white" /> :
                       someOn ? <CheckSquare size={15} className="text-neutral-500" /> :
                       <Square size={15} />}
                    </button>
                    <span className="font-semibold text-white text-sm flex-1">{store}</span>
                    <span className="text-xs text-neutral-600">{storeSelected.length}/{sections.length}</span>
                    <button onClick={() => setExpanded(e => ({ ...e, [store]: !e[store] }))}
                      className="text-neutral-600 hover:text-white transition-colors">
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </button>
                  </div>

                  {/* Sections */}
                  {isExpanded && (
                    <div className="divide-y divide-neutral-800/30">
                      {sections.map(sec => (
                        <label key={sec.key}
                          className="flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-neutral-800/20 transition-colors">
                          <div className="text-neutral-500 hover:text-white transition-colors">
                            {selected[store]?.has(sec.key)
                              ? <CheckSquare size={14} className="text-emerald-400" />
                              : <Square size={14} />}
                          </div>
                          <input type="checkbox" className="hidden"
                            checked={selected[store]?.has(sec.key) ?? false}
                            onChange={() => toggleSection(store, sec.key)} />
                          <span className="text-sm text-neutral-300">{sec.label}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {mode === "all" && (
          <div className="flex-1 flex items-center justify-center text-neutral-600 text-sm py-8">
            Se scrapearan todas las tiendas con todas sus secciones.
          </div>
        )}

        {/* Footer */}
        <div className="px-5 py-4 border-t border-neutral-800 flex items-center justify-between gap-3">
          <span className="text-xs text-neutral-600">
            {mode === "custom" ? `${totalSelected} secciones seleccionadas` : "Todas las secciones"}
          </span>
          <div className="flex gap-2">
            <button onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm text-neutral-500 hover:text-white hover:bg-neutral-800 transition-colors">
              Cancelar
            </button>
            <button onClick={handleRun}
              disabled={mode === "custom" && totalSelected === 0}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-neutral-900 text-sm font-semibold hover:bg-neutral-100 transition-colors disabled:opacity-40">
              <Play size={12} fill="currentColor" /> Correr
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ModeBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
        active ? "bg-white text-neutral-900" : "bg-neutral-800 text-neutral-500 hover:text-neutral-200"
      }`}>
      {children}
    </button>
  );
}

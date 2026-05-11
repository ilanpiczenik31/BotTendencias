"use client";

import { useEffect, useState } from "react";
import { api, Run } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import Link from "next/link";
import { X } from "lucide-react";

export default function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState<number | null>(null);

  function load() {
    api.getRuns(50).then(setRuns).finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function handleCancel(id: number) {
    setCancelling(id);
    try {
      await api.cancelRun(id);
      load();
    } catch { /* ignore */ }
    finally { setCancelling(null); }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Corridas</h1>
        <p className="text-neutral-500 mt-0.5 text-sm">Historial de todas las corridas de scraping.</p>
      </div>

      {loading ? (
        <div className="text-center py-20 text-neutral-700 text-sm">Cargando...</div>
      ) : runs.length === 0 ? (
        <div className="text-center py-20 text-neutral-700 text-sm">Sin corridas aún.</div>
      ) : (
        <div className="rounded-xl border border-neutral-800/60 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800/60 bg-neutral-900/50">
                {["ID", "Fecha", "Estado", "Origen", "Completado", ""].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-neutral-600 uppercase tracking-widest">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} className="border-b border-neutral-800/30 hover:bg-neutral-900/40 transition-colors">
                  <td className="px-4 py-3 text-neutral-600 font-mono text-xs">#{run.id}</td>
                  <td className="px-4 py-3 text-neutral-300">
                    {format(new Date(run.run_date), "dd MMM yyyy · HH:mm", { locale: es })}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${statusStyle(run.status)}`}>
                      {run.status === "running" ? "⏳ running" : run.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-neutral-500 text-xs">{run.triggered_by}</td>
                  <td className="px-4 py-3 text-neutral-500 text-xs font-mono">
                    {run.completed_at ? format(new Date(run.completed_at), "HH:mm:ss") : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {run.status === "completed" && (
                        <Link href={`/runs/${run.id}`} className="text-xs text-neutral-500 hover:text-white transition-colors">
                          Ver →
                        </Link>
                      )}
                      {(run.status === "running" || run.status === "pending") && (
                        <button
                          onClick={() => handleCancel(run.id)}
                          disabled={cancelling === run.id}
                          className="flex items-center gap-1 text-xs text-red-600 hover:text-red-400 transition-colors disabled:opacity-50"
                        >
                          <X size={11} /> {cancelling === run.id ? "Cancelando..." : "Cancelar"}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function statusStyle(s: string) {
  const m: Record<string, string> = {
    completed: "bg-emerald-950 text-emerald-400",
    running:   "bg-blue-950 text-blue-400",
    failed:    "bg-red-950 text-red-500",
    pending:   "bg-yellow-950 text-yellow-400",
  };
  return m[s] ?? "bg-neutral-800 text-neutral-500";
}

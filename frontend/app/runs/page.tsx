"use client";

import { useEffect, useState } from "react";
import { api, Run } from "@/lib/api";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import Link from "next/link";

export default function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRuns(50).then(setRuns).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Corridas</h1>

      {loading ? (
        <div className="text-center py-20 text-neutral-500 text-sm">Cargando...</div>
      ) : runs.length === 0 ? (
        <div className="text-center py-20 text-neutral-500 text-sm">Sin corridas aún.</div>
      ) : (
        <div className="rounded-xl border border-neutral-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800 bg-neutral-900">
                <th className="text-left px-4 py-3 text-xs font-medium text-neutral-400 uppercase tracking-wide">ID</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-neutral-400 uppercase tracking-wide">Fecha</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-neutral-400 uppercase tracking-wide">Estado</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-neutral-400 uppercase tracking-wide">Origen</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-neutral-400 uppercase tracking-wide">Completado</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {runs.map((run, i) => (
                <tr key={run.id} className={`border-b border-neutral-800 ${i % 2 === 0 ? "bg-neutral-950" : "bg-neutral-900"}`}>
                  <td className="px-4 py-3 text-neutral-400">#{run.id}</td>
                  <td className="px-4 py-3 text-neutral-200">
                    {format(new Date(run.run_date), "dd MMM yyyy HH:mm", { locale: es })}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusStyle(run.status)}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-neutral-400">{run.triggered_by}</td>
                  <td className="px-4 py-3 text-neutral-400">
                    {run.completed_at
                      ? format(new Date(run.completed_at), "HH:mm:ss", { locale: es })
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {run.status === "completed" && (
                      <Link href={`/runs/${run.id}`} className="text-xs text-neutral-400 hover:text-white underline">
                        Ver →
                      </Link>
                    )}
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

function statusStyle(status: string) {
  const s: Record<string, string> = {
    completed: "bg-emerald-900 text-emerald-300",
    running: "bg-blue-900 text-blue-300",
    failed: "bg-red-900 text-red-300",
    pending: "bg-yellow-900 text-yellow-300",
  };
  return s[status] ?? "bg-neutral-800 text-neutral-400";
}

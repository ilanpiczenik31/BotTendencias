"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";
import { Lock, Loader2, TrendingUp } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!password.trim()) return;
    setLoading(true);
    setError("");
    try {
      const { token } = await api.login(password.trim());
      setToken(token);
      router.push("/");
    } catch {
      setError("Contraseña incorrecta. Intentá de nuevo.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-8">

        {/* Logo */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-white/5 border border-white/10 mb-2">
            <TrendingUp size={24} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">BotTendencias</h1>
          <p className="text-neutral-500 text-sm">Backoffice · Ingresá tu contraseña para continuar</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <Lock size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-600" />
            <input
              type="password"
              value={password}
              onChange={e => { setPassword(e.target.value); setError(""); }}
              placeholder="Contraseña"
              autoFocus
              className="w-full bg-neutral-900 border border-neutral-800 text-neutral-100 text-sm rounded-xl pl-10 pr-4 py-3 focus:outline-none focus:border-neutral-600 transition-colors placeholder:text-neutral-600"
            />
          </div>

          {error && (
            <p className="text-sm text-red-400 text-center">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !password.trim()}
            className="w-full flex items-center justify-center gap-2 bg-white text-neutral-900 text-sm font-semibold py-3 rounded-xl hover:bg-neutral-100 transition-colors disabled:opacity-50"
          >
            {loading ? <Loader2 size={15} className="animate-spin" /> : "Ingresar"}
          </button>
        </form>

      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { api, Run } from "@/lib/api";
import { isLoggedIn, clearToken } from "@/lib/auth";
import { LogOut, Loader2, TrendingUp } from "lucide-react";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checked, setChecked] = useState(false);
  const [activeRun, setActiveRun] = useState<Run | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isLoginPage = pathname === "/login";

  // Auth check
  useEffect(() => {
    if (!isLoginPage && !isLoggedIn()) {
      router.replace("/login");
    }
    setChecked(true);
  }, [pathname]);

  // Poll for active runs every 3s (shown as global banner)
  useEffect(() => {
    if (isLoginPage || !isLoggedIn()) return;

    async function checkRun() {
      try {
        const runs = await api.getRuns(3);
        const running = runs.find(r => r.status === "running" || r.status === "pending");
        setActiveRun(running ?? null);
      } catch { /* silent */ }
    }

    checkRun();
    pollRef.current = setInterval(checkRun, 3000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [isLoginPage, pathname]);

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  if (!checked) return null;
  if (!isLoginPage && !isLoggedIn()) return null;
  if (isLoginPage) return <>{children}</>;

  return (
    <>
      {/* Navbar */}
      <nav className="border-b border-white/5 bg-black/60 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-5 h-12 flex items-center gap-1">
          <Link href="/" className="font-bold text-white text-sm flex items-center gap-2 mr-5">
            <TrendingUp size={15} className="text-white" />
            <span className="tracking-tight">BotTendencias</span>
            <span className="text-xs bg-white/10 text-neutral-400 px-1.5 py-0.5 rounded font-normal ml-0.5">Admin</span>
          </Link>
          <NavLink href="/">Dashboard</NavLink>
          <NavLink href="/trends">Productos</NavLink>
          <NavLink href="/analysis">Análisis</NavLink>
          <NavLink href="/stores">Tiendas</NavLink>
          <NavLink href="/runs">Historial</NavLink>
          <div className="ml-auto flex items-center gap-3">
            {activeRun && (
              <span className="hidden sm:flex items-center gap-1.5 text-xs text-blue-400 bg-blue-950/40 border border-blue-800/30 px-2.5 py-1 rounded-full">
                <Loader2 size={11} className="animate-spin" />
                Corrida #{activeRun.id} en progreso
              </span>
            )}
            <button
              onClick={handleLogout}
              title="Cerrar sesión"
              className="flex items-center gap-1.5 text-xs text-neutral-600 hover:text-neutral-300 transition-colors p-1.5 rounded-lg hover:bg-white/5"
            >
              <LogOut size={13} />
              <span className="hidden sm:inline">Salir</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Active run banner */}
      {activeRun && (
        <div className="bg-blue-950/30 border-b border-blue-800/20">
          <div className="max-w-6xl mx-auto px-5 h-8 flex items-center gap-2">
            <Loader2 size={12} className="animate-spin text-blue-400 shrink-0" />
            <p className="text-xs text-blue-300">
              Corrida #{activeRun.id} en progreso — actualizando cada 3 segundos
            </p>
            <Link href={`/runs/${activeRun.id}`} className="ml-auto text-xs text-blue-400 hover:text-blue-200 underline shrink-0">
              Ver detalle →
            </Link>
          </div>
        </div>
      )}

      <main className="max-w-6xl mx-auto px-5 py-8">{children}</main>
    </>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const pathname = usePathname();
  const active = pathname === href || (href !== "/" && pathname.startsWith(href));
  return (
    <Link
      href={href}
      className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
        active
          ? "text-white bg-white/8 font-medium"
          : "text-neutral-500 hover:text-white hover:bg-white/5"
      }`}
    >
      {children}
    </Link>
  );
}

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TrendEuropa — Fashion Tracker",
  description: "Rastreador semanal de tendencias de moda europea",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className={`${inter.className} bg-[#0a0a0a] text-neutral-100 min-h-screen`}>
        <nav className="border-b border-white/5 bg-black/60 backdrop-blur-xl sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-5 h-13 flex items-center gap-1">
            <Link href="/" className="font-bold text-white text-sm flex items-center gap-2 mr-5">
              <span className="text-base">👗</span>
              <span className="tracking-tight">TrendEuropa</span>
            </Link>
            <NavLink href="/">Dashboard</NavLink>
            <NavLink href="/trends">Tendencias</NavLink>
            <NavLink href="/history">Histórico</NavLink>
            <NavLink href="/runs">Corridas</NavLink>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-5 py-8">{children}</main>
      </body>
    </html>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href}
      className="px-3 py-1.5 rounded-md text-sm text-neutral-500 hover:text-white hover:bg-white/5 transition-colors">
      {children}
    </Link>
  );
}

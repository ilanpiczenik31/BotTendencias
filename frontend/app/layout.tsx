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
      <body className={`${inter.className} bg-neutral-950 text-neutral-100 min-h-screen`}>
        <nav className="border-b border-neutral-800 bg-neutral-900/80 backdrop-blur sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 h-14 flex items-center gap-2">
            <Link href="/" className="font-bold text-white tracking-tight text-lg flex items-center gap-2 mr-4">
              <span>👗</span> TrendEuropa
            </Link>
            <NavLink href="/">Dashboard</NavLink>
            <NavLink href="/trends">Tendencias</NavLink>
            <NavLink href="/history">Histórico</NavLink>
            <NavLink href="/runs">Corridas</NavLink>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3 py-1.5 rounded-md text-sm text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
    >
      {children}
    </Link>
  );
}

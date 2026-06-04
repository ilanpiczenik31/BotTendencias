import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ClientLayout from "@/components/ClientLayout";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "BotTendencias — Backoffice",
  description: "Panel de administración para rastreo de tendencias de moda europea",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className={`${inter.className} bg-[#0a0a0a] text-neutral-100 min-h-screen`}>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}

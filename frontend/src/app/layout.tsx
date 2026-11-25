import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Career Hunter AI — Central Inteligente de Recolocação Profissional",
  description:
    "Plataforma SaaS com agentes de IA supervisionados para profissionais de analista a diretoria.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">
        {children}
      </body>
    </html>
  );
}

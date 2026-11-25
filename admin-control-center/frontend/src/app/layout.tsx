import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Career Hunter AI — Admin Control Center",
  description: "Central executiva independente de gestão e monitoramento SaaS.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className="h-full antialiased">
      <body className="min-h-full bg-[#f5f7fa] text-[#10172a]">{children}</body>
    </html>
  );
}

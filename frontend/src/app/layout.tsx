import type { Metadata } from "next";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://career-hunter-ai-pink.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "Career Hunter AI | Sua carreira. Nossa inteligência.",
  description:
    "Encontre vagas compatíveis com seu perfil, automatize suas buscas, personalize seu currículo e prepare candidaturas estratégicas com inteligência artificial.",
  openGraph: {
    type: "website",
    locale: "pt_BR",
    url: "/",
    siteName: "Career Hunter AI",
    title: "Career Hunter AI | Sua carreira. Nossa inteligência.",
    description:
      "Encontre vagas compatíveis com seu perfil, automatize suas buscas, personalize seu currículo e prepare candidaturas estratégicas com inteligência artificial.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Career Hunter AI — Procurar emprego não deveria ser um trabalho em tempo integral.",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Career Hunter AI | Sua carreira. Nossa inteligência.",
    description:
      "Encontre vagas compatíveis com seu perfil, automatize suas buscas, personalize seu currículo e prepare candidaturas estratégicas com inteligência artificial.",
    images: ["/og-image.png"],
  },
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

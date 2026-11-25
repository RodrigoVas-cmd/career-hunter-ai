"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Clock } from "lucide-react";
import AppShell from "@/components/AppShell";

const SECTION_META: Record<string, { title: string; phase: string; desc: string }> = {
  entrevistas: {
    title: "Entrevistas (Interview Coach)",
    phase: "Fase 5 — Inteligência Avançada",
    desc: "Preparação com método STAR, resumo verificável da empresa e checklist.",
  },
  relatorios: {
    title: "Relatórios",
    phase: "Fases 2 e 5 — Analytics",
    desc: "Indicadores de conversão, coorte e exportação em CSV, XLSX e PDF.",
  },
  assinatura: {
    title: "Minha Assinatura",
    phase: "Fase 4 — Comercialização",
    desc: "Gestão de plano (Free, Pro, Premium), consumo de quotas e faturamento.",
  },
};

function RoadmapSectionContent() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug || "";
  const info = SECTION_META[slug] || {
    title: "Módulo em desenvolvimento",
    phase: "Próximas fases",
    desc: "Esta área faz parte do roadmap incremental do Career Hunter AI.",
  };

  return (
    <AppShell>
      <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm max-w-2xl">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold">
          <Clock className="h-3.5 w-3.5" />
          {info.phase}
        </span>
        <h1 className="mt-4 text-2xl font-bold text-slate-900">{info.title}</h1>
        <p className="mt-2 text-sm text-slate-600">{info.desc}</p>
        <p className="mt-4 text-xs text-slate-500">
          Seguindo a política de transparência do projeto, não exibimos dados simulados como se
          fossem reais. Conclua seu Perfil Verificado, Cargos-Alvo e Minhas Empresas na Fase 1.
        </p>
        <div className="mt-6">
          <Link
            href="/app"
            className="inline-block px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700"
          >
            Voltar para Visão Geral
          </Link>
        </div>
      </div>
    </AppShell>
  );
}

export default function RoadmapSectionPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-50" />}>
      <RoadmapSectionContent />
    </Suspense>
  );
}

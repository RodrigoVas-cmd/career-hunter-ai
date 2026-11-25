"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { CheckCircle2, Clock } from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, PlanStatus } from "@/lib/api";

const SECTION_META: Record<string, { title: string; phase: string; desc: string }> = {
  entrevistas: {
    title: "Entrevistas (Interview Coach)",
    phase: "Fase 4 — Inteligência Avançada",
    desc: "Preparação com método STAR, resumo verificável da empresa e checklist.",
  },
  relatorios: {
    title: "Relatórios",
    phase: "Fases 2 e 5 — Analytics",
    desc: "Indicadores de conversão, coorte e exportação em CSV, XLSX e PDF.",
  },
  assinatura: {
    title: "Minha Assinatura",
    phase: "Plano e Consumo Mensal",
    desc: "Acompanhe seu plano atual e a franquia mensal de análises.",
  },
};

function RoadmapSectionContent() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug || "";
  const [plan, setPlan] = useState<PlanStatus | null>(null);

  useEffect(() => {
    if (slug === "assinatura") {
      api
        .getDashboardSummary()
        .then((s) => setPlan(s.plan || null))
        .catch(() => {});
    }
  }, [slug]);

  const info = SECTION_META[slug] || {
    title: "Módulo em desenvolvimento",
    phase: "Próximas fases",
    desc: "Esta área faz parte do roadmap incremental do Career Hunter AI.",
  };

  if (slug === "assinatura" && plan) {
    return (
      <AppShell>
        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm max-w-2xl space-y-5">
          <div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 text-[#5035f5] text-xs font-semibold">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Plano Ativo: {plan.plan_name}
            </span>
            <h1 className="mt-3 text-2xl font-bold text-[#10172a]">{info.title}</h1>
            <p className="mt-1 text-sm text-slate-600">{info.desc}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex justify-between text-sm font-semibold text-slate-800">
              <span>Análises de vagas no mês</span>
              <span>
                {plan.monthly_analyses_used} / {plan.monthly_analyses_limit}
              </span>
            </div>
            <div className="w-full h-2.5 rounded-full bg-slate-200 overflow-hidden">
              <div
                className="h-full bg-[#5035f5]"
                style={{
                  width: `${Math.min(
                    100,
                    Math.round(
                      (plan.monthly_analyses_used / Math.max(1, plan.monthly_analyses_limit)) * 100
                    )
                  )}%`,
                }}
              />
            </div>
            <p className="text-xs text-slate-500">
              Restantes este mês: {plan.monthly_analyses_remaining} análise(s). Renovação mensal automática no início de cada mês.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link
              href="/#planos"
              className="px-4 py-2 rounded-xl bg-[#5035f5] text-white text-sm font-semibold hover:bg-indigo-700"
            >
              Comparar planos (Free, Pro, Premium)
            </Link>
            <Link
              href="/app"
              className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-sm font-semibold hover:bg-slate-50"
            >
              Voltar para Visão Geral
            </Link>
          </div>
        </div>
      </AppShell>
    );
  }

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

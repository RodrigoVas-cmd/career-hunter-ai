"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Briefcase,
  Building2,
  CalendarCheck2,
  CheckCircle2,
  FileText,
  Radar,
  Send,
  ShieldCheck,
  Target,
  UserCheck,
  XCircle,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, DashboardSummary } from "@/lib/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    api.getDashboardSummary().then(setSummary).catch(() => {});
  }, []);

  const counts = summary?.counts;
  const totalApps = counts?.applications ?? 0;
  const sentApps = counts?.sent_applications ?? 0;
  const pendingApps = counts?.pending_applications ?? 0;
  const interviewApps = counts?.interview_applications ?? 0;
  const rejectedApps = counts?.rejected_applications ?? 0;

  const funnelCards = [
    {
      label: "Candidaturas Enviadas",
      value: sentApps,
      helper:
        pendingApps > 0
          ? `${pendingApps} em preparação/pendente · ${totalApps} no total`
          : `${totalApps} candidatura(s) registrada(s)`,
      href: "/app/candidaturas",
      icon: Send,
      tone: "border-indigo-200 bg-indigo-50/40 text-indigo-700",
    },
    {
      label: "Avançaram para Entrevista",
      value: interviewApps,
      helper: interviewApps > 0 ? "Ótimo ritmo! Acompanhe no Pipeline" : "Nenhuma entrevista marcada ainda",
      href: "/app/pipeline",
      icon: CalendarCheck2,
      tone: "border-emerald-200 bg-emerald-50/40 text-emerald-700",
    },
    {
      label: "Processos Encerrados",
      value: rejectedApps,
      helper: "Vagas não selecionadas ou finalizadas",
      href: "/app/pipeline",
      icon: XCircle,
      tone: "border-slate-200 bg-slate-50/70 text-slate-600",
    },
    {
      label: "Vagas Compatíveis (≥65%)",
      value: counts?.compatible_jobs ?? 0,
      helper: "Oportunidades prontas para candidatura",
      href: "/app/recomendadas",
      icon: Briefcase,
      tone: "border-violet-200 bg-violet-50/40 text-violet-700",
    },
  ];

  const prepCards = [
    {
      label: "Vagas no Radar",
      value: counts?.discovered_jobs ?? 0,
      href: "/app/radar",
      icon: Radar,
    },
    {
      label: "Cargos-Alvo Ativos",
      value: counts?.target_roles ?? 0,
      href: "/app/cargos",
      icon: Target,
    },
    {
      label: "Empresas Favoritas",
      value: counts?.favorite_companies ?? 0,
      href: "/app/empresas",
      icon: Building2,
    },
    {
      label: "Experiências Validadas",
      value: `${counts?.verified_experiences ?? 0} / ${counts?.experiences ?? 0}`,
      href: "/app/perfil",
      icon: UserCheck,
    },
    {
      label: "Currículos Salvos",
      value: counts?.resumes ?? 0,
      href: "/app/curriculos",
      icon: FileText,
    },
  ];

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              Olá, {summary?.user.full_name || "profissional"}
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              Acompanhe em um só lugar suas candidaturas, entrevistas e novas oportunidades.
            </p>
          </div>
          <Link
            href="/app/recomendadas"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 self-start sm:self-auto"
          >
            <CheckCircle2 className="h-4 w-4" /> Ver vagas recomendadas
          </Link>
        </div>

        <div className="p-4 rounded-2xl bg-indigo-50 border border-indigo-200 flex items-start gap-3">
          <ShieldCheck className="h-5 w-5 text-indigo-600 shrink-0 mt-0.5" />
          <div className="text-sm text-indigo-900">
            <strong>Modo Supervisionado Ativo:</strong> Seus dados ficam protegidos na sua conta e
            nenhuma candidatura é enviada sem a sua aprovação.
          </div>
        </div>

        {/* Funil de Candidaturas */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wide">
              Resumo das suas candidaturas
            </h2>
            <Link href="/app/pipeline" className="text-xs font-semibold text-indigo-600 hover:underline">
              Abrir Pipeline completo →
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {funnelCards.map((card) => {
              const Icon = card.icon;
              return (
                <Link
                  key={card.label}
                  href={card.href}
                  className={`p-5 rounded-2xl border shadow-sm hover:shadow-md transition ${card.tone}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold">{card.label}</span>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="mt-3 text-3xl font-extrabold text-slate-900">{card.value}</div>
                  <div className="mt-1 text-[11px] text-slate-600">{card.helper}</div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Base do Perfil & Preparação */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wide">
            Sua base estratégica
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {prepCards.map((card) => {
              const Icon = card.icon;
              return (
                <Link
                  key={card.label}
                  href={card.href}
                  className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm hover:border-indigo-300 transition"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-500">{card.label}</span>
                    <Icon className="h-4 w-4 text-indigo-600" />
                  </div>
                  <div className="mt-2 text-xl font-bold text-slate-900">{card.value}</div>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          {summary?.user.onboarding_completed ? (
            <>
              <div className="flex items-center justify-between gap-2">
                <h2 className="text-base font-bold text-slate-900">
                  O que você quer fazer agora?
                </h2>
                <Link
                  href="/app/perfil"
                  className="text-xs font-semibold text-indigo-600 hover:underline"
                >
                  Editar perfil ou currículo
                </Link>
              </div>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Link
                  href="/app/radar"
                  className="p-4 rounded-xl border border-slate-200 hover:bg-slate-50 transition"
                >
                  <div className="text-sm font-semibold">1. Buscar novas vagas</div>
                  <p className="text-xs text-slate-500 mt-1">
                    Encontre oportunidades alinhadas ao seu perfil ou cadastre uma vaga de interesse.
                  </p>
                </Link>
                <Link
                  href="/app/recomendadas"
                  className="p-4 rounded-xl border border-slate-200 hover:bg-slate-50 transition"
                >
                  <div className="text-sm font-semibold">2. Preparar candidatura ATS</div>
                  <p className="text-xs text-slate-500 mt-1">
                    Veja sua aderência com a vaga, gere o currículo adaptado e responda ao formulário.
                  </p>
                </Link>
                <Link
                  href="/app/pipeline"
                  className="p-4 rounded-xl border border-slate-200 hover:bg-slate-50 transition"
                >
                  <div className="text-sm font-semibold">3. Acompanhar processos</div>
                  <p className="text-xs text-slate-500 mt-1">
                    Atualize envios, registre entrevistas e acompanhe retornos das empresas.
                  </p>
                </Link>
              </div>
            </>
          ) : (
            <>
              <h2 className="text-base font-bold text-slate-900">
                Complete sua configuração inicial
              </h2>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Link
                  href="/app/curriculos"
                  className="p-4 rounded-xl border border-slate-200 hover:bg-slate-50 transition"
                >
                  <div className="text-sm font-semibold">
                    {(counts?.resumes ?? 0) > 0 ? "✓ Currículo importado" : "1. Importar e validar currículo"}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Envie seu PDF ou DOCX e confirme suas experiências no Perfil Verificado.
                  </p>
                </Link>
                <Link
                  href="/app/cargos"
                  className="p-4 rounded-xl border border-slate-200 hover:bg-slate-50 transition"
                >
                  <div className="text-sm font-semibold">
                    {(counts?.target_roles ?? 0) > 0 ? "✓ Cargos-alvo configurados" : "2. Configurar cargos-alvo"}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Defina títulos, senioridade, sinônimos e critérios obrigatórios.
                  </p>
                </Link>
                <Link
                  href="/app/empresas"
                  className="p-4 rounded-xl border border-slate-200 hover:bg-slate-50 transition"
                >
                  <div className="text-sm font-semibold">
                    {(counts?.favorite_companies ?? 0) > 0 ? "✓ Empresas preferidas salvas" : "3. Cadastrar Minhas Empresas"}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Adicione manualmente ou importe via CSV as empresas desejadas.
                  </p>
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </AppShell>
  );
}

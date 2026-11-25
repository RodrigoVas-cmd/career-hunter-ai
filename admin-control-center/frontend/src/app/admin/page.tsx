"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AdminShell from "@/components/AdminShell";
import { adminApi, ExecutiveDashboard } from "@/lib/api";

function formatBrl(cents: number) {
  return `R$ ${(cents / 100).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`;
}

export default function ExecutiveDashboardPage() {
  const [period, setPeriod] = useState("30d");
  const [data, setData] = useState<ExecutiveDashboard | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    adminApi
      .getDashboard(period)
      .then(setData)
      .catch((e) => setErr(e?.message || "Erro ao carregar visão executiva."));
  }, [period]);

  const total = data?.users.total || 0;
  const freePct = total > 0 ? Math.round(((data?.users.free || 0) / total) * 1000) / 10 : 0;
  const proPct = total > 0 ? Math.round(((data?.users.pro || 0) / total) * 1000) / 10 : 0;
  const premPct = total > 0 ? Math.round(((data?.users.premium || 0) / total) * 1000) / 10 : 0;

  const usageMax = Math.max(
    1,
    data?.usage.analyses || 0,
    data?.usage.tailored_resumes || 0,
    data?.usage.applications || 0,
    data?.usage.active_jobs || 0
  );

  return (
    <AdminShell>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-[#10172a]">Visão executiva</h1>
            <p className="text-xs text-slate-500">
              Dados reais da plataforma · Sem fabricação de métricas
            </p>
          </div>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700"
          >
            <option value="today">Hoje</option>
            <option value="yesterday">Ontem</option>
            <option value="7d">Últimos 7 dias</option>
            <option value="30d">Últimos 30 dias</option>
            <option value="90d">Últimos 90 dias</option>
            <option value="month">Mês atual</option>
            <option value="prev_month">Mês anterior</option>
            <option value="year">Ano atual</option>
          </select>
        </div>

        {err && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700">
            {err}
          </div>
        )}

        {/* Row 1: Users by Plan (PDF Ref 01) */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Total de usuários", val: data?.users.total ?? 0 },
            { label: "Free", val: data?.users.free ?? 0 },
            { label: "Pro", val: data?.users.pro ?? 0 },
            { label: "Premium", val: data?.users.premium ?? 0 },
          ].map((c) => (
            <div key={c.label} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <div className="text-xs font-medium text-slate-500">{c.label}</div>
              <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-[#10172a]">{c.val}</div>
            </div>
          ))}
        </div>

        {/* Row 2: Financial KPIs (PDF Ref 01) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-xs font-medium text-slate-500">Receita recorrente mensal (comprovada)</div>
            <div className="mt-2 text-2xl font-extrabold text-[#10172a]">
              {formatBrl(data?.financial.verified_mrr_brl_cents ?? 0)}
            </div>
            <div className="mt-1 text-[11px] text-slate-500">
              {data?.financial.has_payment_provider
                ? "Baseada em pagamentos confirmados"
                : "Provedor de pagamento não integrado · Cortesias não somam receita"}
            </div>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-xs font-medium text-slate-500">Conversão para pagos</div>
            <div className="mt-2 text-2xl font-extrabold text-[#10172a]">
              {data?.users.conversion_paid_pct ?? 0}%
            </div>
            <div className="mt-1 text-[11px] text-slate-500">
              Pagantes: {data?.users.modalities.paid ?? 0} · Cortesias: {data?.users.modalities.courtesy ?? 0} · Não classificados: {data?.users.modalities.unclassified ?? 0}
            </div>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-xs font-medium text-slate-500">Custo mensal de IA</div>
            <div className="mt-2 text-2xl font-extrabold text-[#10172a]">
              US$ {(data?.financial.ai_cost_usd ?? 0).toFixed(4)}
            </div>
            <div className="mt-1 text-[11px] text-slate-500">
              {data?.financial.has_ai_cost_telemetry
                ? `${data?.financial.total_tokens ?? 0} tokens registrados`
                : "Telemetria de custo por token ainda não registrada"}
            </div>
          </div>
        </div>

        {/* Row 3: Distribution & Evolution (PDF Ref 01) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="text-sm font-bold text-[#10172a]">Distribuição de usuários</h2>
            <div className="mt-5 flex flex-col sm:flex-row items-center gap-6">
              <div
                className="h-36 w-36 rounded-full flex items-center justify-center shrink-0"
                style={{
                  background: `conic-gradient(#c7d2fe 0% ${freePct}%, #5035f5 ${freePct}% ${
                    freePct + proPct
                  }%, #10172a ${freePct + proPct}% 100%)`,
                }}
              >
                <div className="h-24 w-24 rounded-full bg-white flex flex-col items-center justify-center">
                  <span className="text-xl font-extrabold text-[#10172a]">{total}</span>
                  <span className="text-[10px] text-slate-500">usuários</span>
                </div>
              </div>
              <div className="space-y-2.5 text-xs">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-sm bg-[#c7d2fe]" />
                  <span>Free {freePct}% ({data?.users.free ?? 0})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-sm bg-[#5035f5]" />
                  <span>Pro {proPct}% ({data?.users.pro ?? 0})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-sm bg-[#10172a]" />
                  <span>Premium {premPct}% ({data?.users.premium ?? 0})</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="text-sm font-bold text-[#10172a]">Evolução de usuários</h2>
            {!data || data.evolution.length === 0 ? (
              <div className="mt-8 text-xs text-slate-500 text-center">
                Nenhum cadastro registrado até o momento.
              </div>
            ) : (
              <div className="mt-5 space-y-2">
                {data.evolution.map((pt) => (
                  <div key={pt.month} className="flex items-center gap-3 text-xs">
                    <span className="w-16 font-medium text-slate-600">{pt.month}</span>
                    <div className="flex-1 h-2.5 rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className="h-full bg-[#5035f5]"
                        style={{ width: `${Math.min(100, Math.round((pt.users / Math.max(1, total)) * 100))}%` }}
                      />
                    </div>
                    <span className="w-10 text-right font-bold">{pt.users}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Row 4: Platform Usage (PDF Ref 01) */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-[#10172a]">Utilização da plataforma</h2>
            <Link href="/admin/usuarios" className="text-xs font-semibold text-[#5035f5] hover:underline">
              Gerenciar usuários →
            </Link>
          </div>
          {[
            { label: "Análises de aderência", value: data?.usage.analyses ?? 0 },
            { label: "Currículos personalizados", value: data?.usage.tailored_resumes ?? 0 },
            { label: "Candidaturas preparadas", value: data?.usage.applications ?? 0 },
            { label: "Vagas ativas no Radar", value: data?.usage.active_jobs ?? 0 },
          ].map((item) => (
            <div key={item.label} className="space-y-1">
              <div className="flex justify-between text-xs font-medium text-slate-700">
                <span>{item.label}</span>
                <span className="font-bold">{item.value}</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full bg-[#5035f5]"
                  style={{ width: `${Math.min(100, Math.round((item.value / usageMax) * 100))}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </AdminShell>
  );
}

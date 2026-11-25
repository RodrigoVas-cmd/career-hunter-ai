"use client";

import { useEffect, useState } from "react";
import AdminShell from "@/components/AdminShell";
import { adminApi } from "@/lib/api";

export default function ProfitabilityPage() {
  const [data, setData] = useState<{
    plans: Array<{
      plan_code: string;
      plan_name: string;
      price_brl_cents: number;
      paying_users: number;
      courtesy_users: number;
      unclassified_users: number;
      verified_revenue_brl_cents: number;
      ai_cost_usd: number;
    }>;
    total_operational_costs_brl_cents: number;
    note: string;
  } | null>(null);

  useEffect(() => {
    adminApi.getProfitability().then(setData).catch(() => {});
  }, []);

  return (
    <AdminShell>
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-[#10172a]">Rentabilidade por plano</h1>
          <p className="text-xs text-slate-500 mt-1">
            {data?.note || "Apuração real por plano separando pagantes comprovados, cortesias e custos."}
          </p>
        </div>

        <div className="space-y-6">
          {(data?.plans || []).map((p) => {
            const revBrl = p.verified_revenue_brl_cents / 100;
            return (
              <div key={p.plan_code} className="space-y-2 border-b border-slate-100 pb-5 last:border-0">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-base text-[#10172a]">{p.plan_name}</div>
                  <div className="text-xs text-slate-500">
                    Pagantes: <strong>{p.paying_users}</strong> · Cortesias: <strong>{p.courtesy_users}</strong> · Não classificados:{" "}
                    <strong>{p.unclassified_users}</strong>
                  </div>
                </div>
                <div className="flex justify-between text-xs text-slate-600">
                  <span>Receita comprovada</span>
                  <span className="font-bold">R$ {revBrl.toFixed(2).replace(".", ",")}</span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full bg-[#5035f5]"
                    style={{ width: revBrl > 0 ? "70%" : "2%" }}
                  />
                </div>
                <div className="flex justify-between text-xs text-slate-600">
                  <span>Custo de IA registrado</span>
                  <span className="font-bold text-amber-600">US$ {p.ai_cost_usd.toFixed(4)}</span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="text-xs text-slate-500 pt-2 border-t border-slate-100">
          Custos operacionais cadastrados: R${" "}
          {((data?.total_operational_costs_brl_cents || 0) / 100).toFixed(2).replace(".", ",")} / mês · Não contempla impostos e taxas ainda não informadas.
        </div>
      </div>
    </AdminShell>
  );
}

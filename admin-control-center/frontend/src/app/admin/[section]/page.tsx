"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AdminShell from "@/components/AdminShell";
import { adminApi } from "@/lib/api";

const TITLES: Record<string, string> = {
  assinaturas: "Assinaturas e Pagamentos",
  planos: "Planos, Preços e Limites",
  ia: "Central de Inteligência Artificial",
  buscas: "Monitoramento de Buscas",
  comercial: "Inteligência Comercial",
  cupons: "Cupons e Cortesias",
  prompts: "Gestão de Agentes e Prompts",
  suporte: "Suporte e Comunicações",
  auditoria: "Auditoria e Segurança",
  configuracoes: "Configurações Administrativas",
};

export default function AdminSectionPage() {
  const params = useParams<{ section: string }>();
  const section = params?.section || "";
  const [payload, setPayload] = useState<unknown>(null);

  useEffect(() => {
    if (section === "planos") adminApi.listPlans().then(setPayload).catch(() => {});
    else if (section === "assinaturas") adminApi.listSubscriptions().then(setPayload).catch(() => {});
    else if (section === "cupons") adminApi.listCourtesies().then(setPayload).catch(() => {});
    else if (section === "ia") adminApi.getAiCenter().then(setPayload).catch(() => {});
    else if (section === "buscas") adminApi.getSearches().then(setPayload).catch(() => {});
    else if (section === "prompts") adminApi.listPrompts().then(setPayload).catch(() => {});
    else if (section === "suporte") adminApi.listSupport().then(setPayload).catch(() => {});
    else if (section === "auditoria") adminApi.listAuditLogs().then(setPayload).catch(() => {});
  }, [section]);

  return (
    <AdminShell>
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h1 className="text-xl font-bold text-[#10172a]">
          {TITLES[section] || "Módulo Administrativo"}
        </h1>

        {section === "planos" && Array.isArray(payload) && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {payload.map((p: Record<string, unknown>) => (
              <div key={String(p.code)} className="p-5 rounded-2xl border border-slate-200 space-y-2">
                <div className="font-bold text-base">{String(p.name)}</div>
                <div className="text-xl font-extrabold text-[#5035f5]">
                  R$ {(Number(p.price_brl_cents || 0) / 100).toFixed(2).replace(".", ",")}/mês
                </div>
                <div className="text-xs text-slate-500">
                  Assinaturas ativas: {String(p.active_subscribers_count ?? 0)}
                </div>
                <pre className="text-[11px] bg-slate-50 p-2 rounded-lg overflow-auto">
                  {JSON.stringify(p.features, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}

        {section !== "planos" && (
          <pre className="text-xs bg-slate-50 border border-slate-200 rounded-xl p-4 overflow-auto max-h-[540px]">
            {payload
              ? JSON.stringify(payload, null, 2)
              : "Sem registros no momento ou módulo aguardando telemetria/integração."}
          </pre>
        )}
      </div>
    </AdminShell>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ShieldAlert } from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { adminApi, AdminApiError, AdminUserDetail, getAdminToken } from "@/lib/api";

export default function UserDetailPage() {
  const params = useParams<{ id: string }>();
  const userId = params?.id || "";
  const [user, setUser] = useState<AdminUserDetail | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Modal: Gerenciar plano
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [planAction, setPlanAction] = useState("change_plan");
  const [planCode, setPlanCode] = useState("pro");
  const [modality, setModality] = useState("courtesy");
  const [durationType, setDurationType] = useState("30d");
  const [customDays, setCustomDays] = useState("45");
  const [creditMetric, setCreditMetric] = useState("job_analysis");
  const [creditAmount, setCreditAmount] = useState("10");
  const [justification, setJustification] = useState("");

  function load() {
    if (!userId) return;
    adminApi
      .getUserDetail(userId)
      .then((d) => {
        setUser(d);
        setPlanCode(d.plan_code);
        setModality(d.access_modality);
      })
      .catch((e) => setErr(e?.message || "Erro ao carregar ficha."));
  }

  useEffect(() => {
    load();
  }, [userId]);

  async function handlePlanSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    try {
      await adminApi.managePlan(userId, {
        action: planAction,
        plan_code: planCode,
        access_modality: modality,
        duration_type: durationType,
        custom_days: durationType === "custom" ? Number(customDays) : undefined,
        credit_metric: creditMetric,
        credit_amount: Number(creditAmount),
        justification,
      });
      setShowPlanModal(false);
      setJustification("");
      setMsg("Alteração de plano/benefício registrada com auditoria.");
      load();
    } catch (e2) {
      setErr(e2 instanceof AdminApiError ? e2.message : "Erro ao atualizar plano.");
    }
  }

  async function handlePrivateDownload(docKind: string, docId: string, name: string) {
    const just = window.prompt(
      "Acesso privado auditado: informe a finalidade e justificativa (mín. 5 caracteres):"
    );
    if (!just || just.trim().length < 5) return;
    const token = getAdminToken();
    const res = await fetch(
      `${adminApi.baseUrl}/users/${userId}/documents/${docKind}/${docId}?justification=${encodeURIComponent(
        just.trim()
      )}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} }
    );
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setErr(data?.detail || "Erro ao acessar documento.");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleStatusAction(action: "activate" | "suspend" | "deactivate") {
    const just = window.prompt(`Justificativa obrigatória para ${action}:`);
    if (!just || just.trim().length < 5) return;
    try {
      await adminApi.updateUserStatus(userId, { action, justification: just.trim() });
      setMsg(`Status da conta atualizado (${action}).`);
      load();
    } catch (e2) {
      setErr(e2 instanceof AdminApiError ? e2.message : "Erro ao atualizar status.");
    }
  }

  async function handleLgpdDelete() {
    const just = window.prompt("Justificativa obrigatória para exclusão definitiva LGPD (mín. 8 chars):");
    if (!just || just.trim().length < 8) return;
    const conf = window.prompt('Digite exatamente "EXCLUIR DEFINITIVAMENTE" para confirmar:');
    if (!conf) return;
    try {
      await adminApi.lgpdDeleteUser(userId, {
        confirmation_text: conf,
        justification: just.trim(),
      });
      setMsg("Conta anonimizada e documentos removidos conforme LGPD.");
      load();
    } catch (e2) {
      setErr(e2 instanceof AdminApiError ? e2.message : "Erro ao excluir conta.");
    }
  }

  if (!user) {
    return (
      <AdminShell>
        <div className="text-sm text-slate-500">Carregando ficha individual...</div>
      </AdminShell>
    );
  }

  return (
    <AdminShell>
      <div className="space-y-5">
        <Link
          href="/admin/usuarios"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#5035f5] hover:underline"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Voltar para Gerenciamento de usuários
        </Link>

        {err && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700">{err}</div>
        )}
        {msg && (
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-700">
            {msg}
          </div>
        )}

        {/* Main Card (PDF Ref 03) */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-5">
            <div>
              <h1 className="text-2xl font-bold text-[#10172a]">{user.full_name}</h1>
              <div className="text-sm text-[#5035f5] font-medium mt-0.5">
                {user.email} · {user.plan_name} ·{" "}
                {user.account_status === "active" ? "Ativo" : user.account_status} · Modalidade:{" "}
                {user.access_modality === "unclassified" ? "Não classificada" : user.access_modality}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setShowPlanModal(true)}
              className="px-4 py-2.5 rounded-xl bg-[#5035f5] text-white text-xs font-semibold hover:bg-indigo-700 shrink-0"
            >
              Gerenciar plano
            </button>
          </div>

          {/* 2-col Metadata Grid (PDF Ref 03) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-xs text-slate-500">Data de cadastro</div>
              <div className="font-bold text-[#10172a]">
                {new Date(user.created_at).toLocaleDateString("pt-BR")}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Início da assinatura</div>
              <div className="font-bold text-[#10172a]">
                {user.subscription_start
                  ? new Date(user.subscription_start).toLocaleDateString("pt-BR")
                  : "Sem assinatura"}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Expiração / Próxima renovação</div>
              <div className="font-bold text-[#10172a]">
                {user.courtesy?.expires_at
                  ? `Cortesia até ${new Date(user.courtesy.expires_at).toLocaleDateString("pt-BR")}`
                  : user.next_renewal
                  ? new Date(user.next_renewal).toLocaleDateString("pt-BR")
                  : user.courtesy
                  ? "Prazo indeterminado"
                  : "—"}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Cargo(s) pretendido(s)</div>
              <div className="font-bold text-[#10172a]">
                {user.profile.target_roles.length > 0
                  ? user.profile.target_roles.join(", ")
                  : "Não informado"}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Mensalidade comprovada</div>
              <div className="font-bold text-[#10172a]">
                R$ {(user.plan_price_brl_cents / 100).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Localidade</div>
              <div className="font-bold text-[#10172a]">
                {[user.profile.city, user.profile.state].filter(Boolean).join(" - ") || "—"}
              </div>
            </div>
          </div>

          {/* Documentos profissionais (PDF Ref 03) */}
          <div className="border-t border-slate-100 pt-5 space-y-3">
            <h2 className="text-sm font-bold text-[#10172a]">Documentos profissionais</h2>
            {user.documents.originals.length === 0 && user.documents.ats_versions.length === 0 ? (
              <p className="text-xs text-slate-500">Nenhum documento enviado.</p>
            ) : (
              <div className="space-y-2 text-xs">
                {user.documents.originals.map((d) => (
                  <div key={d.id} className="flex items-center justify-between py-1.5 border-b border-slate-100">
                    <span>
                      <strong>{d.name}</strong> · Original ({d.format.toUpperCase()}) · {d.parse_status}
                    </span>
                    <button
                      type="button"
                      onClick={() => handlePrivateDownload("original", d.id, d.name)}
                      className="text-[#5035f5] font-semibold hover:underline"
                    >
                      Baixar (auditado)
                    </button>
                  </div>
                ))}
                {user.documents.ats_versions.map((rv) => (
                  <div key={rv.id} className="flex items-center justify-between py-1.5 border-b border-slate-100">
                    <span>
                      <strong>{rv.label}</strong> · {rv.approved_by_user ? "Aprovado pelo usuário" : "Em revisão"}
                    </span>
                    <div className="flex gap-3">
                      {rv.has_pdf && (
                        <button
                          type="button"
                          onClick={() => handlePrivateDownload("ats_pdf", rv.id, `${rv.label}.pdf`)}
                          className="text-[#5035f5] font-semibold hover:underline"
                        >
                          Baixar PDF
                        </button>
                      )}
                      {rv.has_docx && (
                        <button
                          type="button"
                          onClick={() => handlePrivateDownload("ats_docx", rv.id, `${rv.label}.docx`)}
                          className="text-[#5035f5] font-semibold hover:underline"
                        >
                          Baixar DOCX
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Consumo mensal (PDF Ref 03) */}
          <div className="border-t border-slate-100 pt-5 space-y-3">
            <h2 className="text-sm font-bold text-[#10172a]">Consumo mensal</h2>
            {[
              {
                label: `Análises de aderência (inclui +${user.usage.extra_analysis_credits} créditos extras)`,
                used: user.usage.analyses_used,
                limit: user.usage.analyses_limit,
              },
              {
                label: "Currículos personalizados",
                used: user.usage.custom_resumes_used,
                limit: user.usage.custom_resumes_limit,
              },
              {
                label: "Candidaturas preparadas",
                used: user.usage.applications_used,
                limit: user.usage.applications_limit,
              },
            ].map((bar) => (
              <div key={bar.label} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-700">{bar.label}</span>
                  <span className="font-bold">
                    {bar.used}/{bar.limit}
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full bg-[#5035f5]"
                    style={{
                      width: `${Math.min(100, Math.round((bar.used / Math.max(1, bar.limit)) * 100))}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Ações administrativas (PDF Ref 03) */}
          <div className="border-t border-slate-100 pt-5 space-y-3">
            <h2 className="text-sm font-bold text-[#10172a]">Ações administrativas</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
              <button
                type="button"
                onClick={() => setShowPlanModal(true)}
                className="px-3 py-2.5 rounded-xl border border-slate-200 font-semibold text-[#10172a] hover:bg-slate-50"
              >
                Gerenciar plano
              </button>
              <button
                type="button"
                onClick={() => {
                  setPlanAction("grant_courtesy");
                  setShowPlanModal(true);
                }}
                className="px-3 py-2.5 rounded-xl border border-slate-200 font-semibold text-[#10172a] hover:bg-slate-50"
              >
                Conceder cortesia
              </button>
              <button
                type="button"
                onClick={() => handleStatusAction("suspend")}
                className="px-3 py-2.5 rounded-xl border border-slate-200 font-semibold text-amber-700 hover:bg-amber-50"
              >
                Suspender conta
              </button>
              <button
                type="button"
                onClick={() => handleStatusAction("activate")}
                className="px-3 py-2.5 rounded-xl border border-slate-200 font-semibold text-emerald-700 hover:bg-emerald-50"
              >
                Reativar conta
              </button>
              <button
                type="button"
                onClick={() => handleStatusAction("deactivate")}
                className="px-3 py-2.5 rounded-xl border border-slate-200 font-semibold text-slate-700 hover:bg-slate-50"
              >
                Desativar conta
              </button>
              <button
                type="button"
                onClick={handleLgpdDelete}
                className="px-3 py-2.5 rounded-xl border border-red-200 font-semibold text-red-600 hover:bg-red-50"
              >
                Excluir conta (LGPD)
              </button>
            </div>
          </div>

          {/* Histórico recente */}
          <div className="border-t border-slate-100 pt-5 space-y-2">
            <h2 className="text-sm font-bold text-[#10172a]">Histórico recente e auditoria</h2>
            {user.history.length === 0 ? (
              <p className="text-xs text-slate-500">Sem eventos registrados.</p>
            ) : (
              <ul className="space-y-1.5 text-xs text-slate-600">
                {user.history.slice(0, 10).map((h, i) => (
                  <li key={i}>
                    • <strong>{h.action}</strong> ({h.source}) — {h.actor}{" "}
                    {h.justification ? `· "${h.justification}"` : ""} ·{" "}
                    {new Date(h.created_at).toLocaleString("pt-BR")}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Modal: Gerenciar plano */}
      {showPlanModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <form
            onSubmit={handlePlanSubmit}
            className="w-full max-w-lg bg-white rounded-2xl border border-slate-200 shadow-xl p-6 space-y-4"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-[#10172a]">Gerenciar plano — {user.full_name}</h3>
              <button
                type="button"
                onClick={() => setShowPlanModal(false)}
                className="text-xs text-slate-500 hover:text-slate-900"
              >
                Fechar
              </button>
            </div>

            <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-[11px] text-amber-800 flex items-start gap-2">
              <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" />
              <span>
                Cortesias administrativas nunca geram cobrança automática nem são contabilizadas como receita paga.
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700">Operação</label>
              <select
                value={planAction}
                onChange={(e) => setPlanAction(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="change_plan">Alterar plano (Upgrade / Downgrade)</option>
                <option value="grant_courtesy">Conceder acesso de cortesia (Pro/Premium)</option>
                <option value="revoke_courtesy">Revogar acesso de cortesia</option>
                <option value="grant_credits">Conceder créditos adicionais</option>
              </select>
            </div>

            {(planAction === "change_plan" || planAction === "grant_courtesy") && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700">Plano</label>
                  <select
                    value={planCode}
                    onChange={(e) => setPlanCode(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                  >
                    {planAction === "change_plan" && <option value="free">Free</option>}
                    <option value="pro">Pro</option>
                    <option value="premium">Premium</option>
                  </select>
                </div>

                {planAction === "change_plan" ? (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700">Modalidade</label>
                    <select
                      value={modality}
                      onChange={(e) => setModality(e.target.value)}
                      className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                    >
                      <option value="free">Free</option>
                      <option value="paid">Pagante (comprovado)</option>
                      <option value="courtesy">Cortesia</option>
                      <option value="unclassified">Não classificado</option>
                    </select>
                  </div>
                ) : (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700">Duração da cortesia</label>
                    <select
                      value={durationType}
                      onChange={(e) => setDurationType(e.target.value)}
                      className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                    >
                      <option value="7d">7 dias</option>
                      <option value="15d">15 dias</option>
                      <option value="30d">30 dias</option>
                      <option value="90d">90 dias</option>
                      <option value="custom">Prazo personalizado</option>
                      <option value="indefinite">Prazo indeterminado</option>
                    </select>
                  </div>
                )}
              </div>
            )}

            {planAction === "grant_courtesy" && durationType === "custom" && (
              <div>
                <label className="block text-xs font-semibold text-slate-700">Dias personalizados</label>
                <input
                  type="number"
                  min={1}
                  max={3650}
                  value={customDays}
                  onChange={(e) => setCustomDays(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            )}

            {planAction === "grant_credits" && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700">Recurso</label>
                  <select
                    value={creditMetric}
                    onChange={(e) => setCreditMetric(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="job_analysis">Análises de aderência</option>
                    <option value="custom_resume">Currículos personalizados</option>
                    <option value="prepared_application">Candidaturas preparadas</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700">Quantidade</label>
                  <input
                    type="number"
                    min={1}
                    max={10000}
                    value={creditAmount}
                    onChange={(e) => setCreditAmount(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700">
                Justificativa obrigatória (registrada em auditoria)
              </label>
              <textarea
                required
                minLength={5}
                rows={2}
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                placeholder="Descreva o motivo administrativo..."
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowPlanModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-300 text-xs font-semibold text-slate-700"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-xl bg-[#5035f5] text-white text-xs font-semibold hover:bg-indigo-700"
              >
                Confirmar alteração
              </button>
            </div>
          </form>
        </div>
      )}
    </AdminShell>
  );
}

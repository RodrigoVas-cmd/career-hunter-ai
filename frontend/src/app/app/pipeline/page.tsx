"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Calendar, Kanban, Table2 } from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, ApplicationItem, InterviewItem } from "@/lib/api";

const KANBAN_COLUMNS = [
  { key: "em_preparacao", label: "Em Preparação", statuses: ["descoberta", "qualificada", "favorita", "em_preparacao"] },
  { key: "revisao_aprovacao", label: "Revisão / Aprovação", statuses: ["aguardando_revisao", "aguardando_aprovacao", "envio_em_andamento", "pendente_confirmacao"] },
  { key: "enviada", label: "Enviada e Confirmada", statuses: ["enviada_confirmada", "resposta_recebida", "teste_solicitado"] },
  { key: "entrevistas", label: "Em Entrevistas", statuses: ["entrevista_agendada", "entrevista_realizada", "proxima_etapa"] },
  { key: "desfecho", label: "Proposta / Encerrada", statuses: ["proposta_recebida", "contratado", "reprovado", "desistencia", "encerrada", "descartada", "falha_envio"] },
];

export default function PipelinePage() {
  const [view, setView] = useState<"kanban" | "table" | "calendar">("kanban");
  const [apps, setApps] = useState<ApplicationItem[]>([]);
  const [interviews, setInterviews] = useState<InterviewItem[]>([]);

  useEffect(() => {
    Promise.all([api.listApplications(), api.listAllInterviews()]).then(([a, iv]) => {
      setApps(a);
      setInterviews(iv);
    });
  }, []);

  async function moveStatus(appId: string, nextStatus: string) {
    const updated = await api.updateApplication(appId, { operational_status: nextStatus });
    setApps((prev) => prev.map((a) => (a.id === appId ? updated : a)));
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">Pipeline · CRM de Recolocação</h1>
            <p className="text-sm text-slate-600">
              Acompanhe suas candidaturas em Kanban, Tabela ou Calendário de entrevistas.
            </p>
          </div>
          <div className="inline-flex rounded-xl border border-slate-200 bg-white p-1">
            <button
              type="button"
              onClick={() => setView("kanban")}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${
                view === "kanban" ? "bg-indigo-600 text-white" : "text-slate-600"
              }`}
            >
              <Kanban className="h-3.5 w-3.5" /> Kanban
            </button>
            <button
              type="button"
              onClick={() => setView("table")}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${
                view === "table" ? "bg-indigo-600 text-white" : "text-slate-600"
              }`}
            >
              <Table2 className="h-3.5 w-3.5" /> Tabela
            </button>
            <button
              type="button"
              onClick={() => setView("calendar")}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${
                view === "calendar" ? "bg-indigo-600 text-white" : "text-slate-600"
              }`}
            >
              <Calendar className="h-3.5 w-3.5" /> Calendário
            </button>
          </div>
        </div>

        {view === "kanban" && (
          <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-4">
            {KANBAN_COLUMNS.map((col) => {
              const items = apps.filter((a) => col.statuses.includes(a.operational_status));
              return (
                <div
                  key={col.key}
                  className="bg-slate-100/80 rounded-2xl p-3 border border-slate-200 space-y-2.5"
                >
                  <div className="flex items-center justify-between px-1">
                    <span className="text-xs font-bold text-slate-700">{col.label}</span>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-white text-slate-600">
                      {items.length}
                    </span>
                  </div>
                  {items.map((item) => (
                    <Link
                      key={item.id}
                      href={`/app/candidaturas?id=${item.id}`}
                      className="block bg-white p-3 rounded-xl border border-slate-200 shadow-sm hover:border-indigo-400 transition"
                    >
                      <div className="text-xs font-bold text-slate-900">{item.role_title}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{item.company_name}</div>
                      <div className="mt-2 text-[10px] px-2 py-0.5 inline-block rounded-full bg-slate-100 text-slate-700">
                        {item.operational_status}
                      </div>
                    </Link>
                  ))}
                </div>
              );
            })}
          </div>
        )}

        {view === "table" && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs text-slate-600">
                <tr>
                  <th className="p-3">Cargo</th>
                  <th className="p-3">Empresa</th>
                  <th className="p-3">Status Operacional</th>
                  <th className="p-3">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {apps.map((a) => (
                  <tr key={a.id}>
                    <td className="p-3 font-semibold">{a.role_title}</td>
                    <td className="p-3 text-slate-600">{a.company_name}</td>
                    <td className="p-3">
                      <select
                        value={a.operational_status}
                        onChange={(e) => moveStatus(a.id, e.target.value)}
                        className="rounded-lg border border-slate-300 px-2 py-1 text-xs"
                      >
                        <option value="em_preparacao">em_preparacao</option>
                        <option value="aguardando_revisao">aguardando_revisao</option>
                        <option value="aguardando_aprovacao">aguardando_aprovacao</option>
                        <option value="enviada_confirmada">enviada_confirmada</option>
                        <option value="resposta_recebida">resposta_recebida</option>
                        <option value="entrevista_agendada">entrevista_agendada</option>
                        <option value="proposta_recebida">proposta_recebida</option>
                        <option value="contratado">contratado</option>
                        <option value="reprovado">reprovado</option>
                        <option value="desistencia">desistencia</option>
                      </select>
                    </td>
                    <td className="p-3">
                      <Link
                        href={`/app/candidaturas?id=${a.id}`}
                        className="text-indigo-600 font-semibold hover:underline"
                      >
                        Abrir
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {view === "calendar" && (
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <h2 className="text-sm font-bold">Agenda de Entrevistas ({interviews.length})</h2>
            {interviews.length === 0 ? (
              <p className="text-xs text-slate-500">Nenhuma entrevista agendada até o momento.</p>
            ) : (
              interviews.map((iv) => (
                <div
                  key={iv.id}
                  className="p-3 rounded-xl border border-slate-200 flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-semibold text-slate-900">{iv.stage_name}</div>
                    <div className="text-slate-500">
                      {iv.scheduled_at
                        ? new Date(iv.scheduled_at).toLocaleString("pt-BR")
                        : "Data a definir"}
                    </div>
                  </div>
                  <Link
                    href={`/app/candidaturas?id=${iv.application_id}`}
                    className="text-indigo-600 font-semibold hover:underline"
                  >
                    Ver candidatura
                  </Link>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}

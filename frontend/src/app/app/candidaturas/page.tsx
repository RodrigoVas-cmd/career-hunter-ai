"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  CheckCircle2,
  ExternalLink,
  FileText,
  Plus,
  Send,
  ShieldCheck,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import {
  api,
  ApiError,
  ApplicationDetail,
  ApplicationItem,
  getToken,
} from "@/lib/api";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function CandidaturasContent() {
  const searchParams = useSearchParams();
  const initialId = searchParams.get("id");

  const [apps, setApps] = useState<ApplicationItem[]>([]);
  const [selected, setSelected] = useState<ApplicationDetail | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Manual application
  const [showNew, setShowNew] = useState(false);
  const [newCompany, setNewCompany] = useState("");
  const [newRole, setNewRole] = useState("");
  const [newUrl, setNewUrl] = useState("");

  // Question
  const [questionText, setQuestionText] = useState("");
  const [fieldType, setFieldType] = useState("texto_longo");
  const [maxChars, setMaxChars] = useState("");
  const [answerDrafts, setAnswerDrafts] = useState<Record<string, string>>({});

  // Interview
  const [ivStage, setIvStage] = useState("");
  const [ivDate, setIvDate] = useState("");

  function loadList(selectId?: string) {
    api.listApplications().then((list) => {
      setApps(list);
      const targetId = selectId || initialId || list[0]?.id;
      if (targetId) {
        loadDetail(targetId);
      }
    });
  }

  function loadDetail(id: string) {
    api.getApplicationDetail(id).then((d) => {
      setSelected(d);
      const drafts: Record<string, string> = {};
      d.answers.forEach((a) => {
        drafts[a.id] = a.approved_answer || a.draft_answer || "";
      });
      setAnswerDrafts(drafts);
    });
  }

  useEffect(() => {
    loadList();
  }, []);

  async function handleCreateManual(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    try {
      const created = await api.createApplication({
        company_name: newCompany,
        role_title: newRole,
        source_url: newUrl || undefined,
        is_manual: true,
      });
      setNewCompany("");
      setNewRole("");
      setNewUrl("");
      setShowNew(false);
      loadList(created.id);
      setMsg("Candidatura criada em preparação.");
    } catch (e2) {
      setErr(e2 instanceof ApiError ? e2.message : "Erro ao criar candidatura.");
    }
  }

  async function handleGenerateAts() {
    if (!selected) return;
    setErr(null);
    setMsg(null);
    try {
      await api.generateAtsResume(selected.id);
      loadDetail(selected.id);
      setMsg("Currículo ATS gerado exclusivamente com fatos verificados.");
    } catch (e2) {
      setErr(e2 instanceof ApiError ? e2.message : "Erro ao gerar currículo ATS.");
    }
  }

  async function handleApproveAts() {
    if (!selected?.resume_version) return;
    await api.approveAtsResume(selected.resume_version.id);
    loadDetail(selected.id);
    setMsg("Versão ATS do currículo aprovada.");
  }

  async function handleDownloadDocx(versionId: string, docxPath?: string | null) {
    const token = getToken();
    const res = await fetch(
      `${API_BASE}/applications/resume-versions/${versionId}/download`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} }
    );
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const fname = docxPath ? docxPath.split(/[/\\]/).pop() : `curriculo-1.docx`;
    a.download = fname || "curriculo-1.docx";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleDownloadPdf(versionId: string, pdfPath?: string | null) {
    const token = getToken();
    const res = await fetch(
      `${API_BASE}/applications/resume-versions/${versionId}/download-pdf`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} }
    );
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const fname = pdfPath ? pdfPath.split(/[/\\]/).pop() : `curriculo_ats_${versionId.slice(0, 8)}-1.pdf`;
    a.download = fname || "curriculo-1.pdf";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleAddQuestion(e: React.FormEvent) {
    e.preventDefault();
    if (!selected || !questionText.trim()) return;
    setErr(null);
    await api.prepareQuestion(selected.id, {
      question_text: questionText.trim(),
      field_type: fieldType,
      max_chars: maxChars ? Number(maxChars) : undefined,
    });
    setQuestionText("");
    setMaxChars("");
    loadDetail(selected.id);
  }

  async function handleSaveAnswer(answerId: string) {
    if (!selected) return;
    const text = (answerDrafts[answerId] || "").trim();
    if (!text) return;
    await api.saveAnswer(answerId, text);
    loadDetail(selected.id);
    setMsg("Resposta salva e aprovada.");
  }

  async function handleApproveApplication() {
    if (!selected) return;
    setErr(null);
    setMsg(null);
    try {
      await api.approveApplication(selected.id);
      loadList(selected.id);
      setMsg("Candidatura aprovada explicitamente para envio supervisionado!");
    } catch (e2) {
      setErr(e2 instanceof ApiError ? e2.message : "Erro ao aprovar candidatura.");
    }
  }

  async function handleConfirmSubmission(ambiguous = false) {
    if (!selected) return;
    setErr(null);
    setMsg(null);
    try {
      await api.confirmSubmission(selected.id, {
        confirmed: !ambiguous,
        ambiguous,
      });
      loadList(selected.id);
      setMsg(
        ambiguous
          ? "Envio marcado como pendente de confirmação."
          : "Envio confirmado e registrado no CRM!"
      );
    } catch (e2) {
      setErr(e2 instanceof ApiError ? e2.message : "Erro ao confirmar envio.");
    }
  }

  async function handleAddInterview(e: React.FormEvent) {
    e.preventDefault();
    if (!selected || !ivStage.trim()) return;
    await api.createInterview(selected.id, {
      stage_name: ivStage.trim(),
      scheduled_at: ivDate ? new Date(ivDate).toISOString() : undefined,
    });
    setIvStage("");
    setIvDate("");
    loadDetail(selected.id);
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">Candidaturas Supervisionadas</h1>
            <p className="text-sm text-slate-600">
              Personalize currículo ATS, revise respostas e aprove individualmente antes de qualquer envio.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowNew((v) => !v)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold"
          >
            <Plus className="h-4 w-4" /> Nova candidatura manual
          </button>
        </div>

        {err && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">
            {err}
          </div>
        )}
        {msg && (
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-sm text-emerald-700">
            {msg}
          </div>
        )}

        {showNew && (
          <form
            onSubmit={handleCreateManual}
            className="bg-white p-5 rounded-2xl border border-indigo-200 grid grid-cols-1 sm:grid-cols-4 gap-3"
          >
            <input
              type="text"
              required
              value={newCompany}
              onChange={(e) => setNewCompany(e.target.value)}
              placeholder="Empresa"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              type="text"
              required
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              placeholder="Cargo"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              type="url"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              placeholder="URL da vaga (opcional)"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              type="submit"
              className="rounded-lg bg-indigo-600 text-white text-sm font-semibold px-4 py-2"
            >
              Criar
            </button>
          </form>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* List */}
          <div className="space-y-2">
            {apps.length === 0 ? (
              <div className="bg-white p-6 rounded-2xl border border-slate-200 text-sm text-slate-500">
                Nenhuma candidatura iniciada. Selecione uma vaga em Vagas Recomendadas ou crie uma manual.
              </div>
            ) : (
              apps.map((a) => (
                <button
                  key={a.id}
                  type="button"
                  onClick={() => loadDetail(a.id)}
                  className={`w-full text-left p-4 rounded-2xl border transition ${
                    selected?.id === a.id
                      ? "bg-indigo-50 border-indigo-500"
                      : "bg-white border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <div className="font-semibold text-sm text-slate-900">{a.role_title}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{a.company_name}</div>
                  <div className="mt-2 flex items-center gap-2 text-[11px]">
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium">
                      {a.operational_status}
                    </span>
                    {a.has_valid_approval && (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-semibold">
                        Aprovada
                      </span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Workspace */}
          {selected && (
            <div className="lg:col-span-2 space-y-5">
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h2 className="text-lg font-bold">{selected.role_title}</h2>
                    <p className="text-xs text-slate-500">
                      {selected.company_name} · Status: <strong>{selected.operational_status}</strong>
                    </p>
                  </div>
                  {selected.source_url && (
                    <a
                      href={selected.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700"
                    >
                      Abrir vaga oficial <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>

                {/* ATS Resume Section */}
                <div className="border-t border-slate-100 pt-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold flex items-center gap-2">
                      <FileText className="h-4 w-4 text-indigo-600" />
                      1. Currículo Personalizado para ATS
                    </h3>
                    <button
                      type="button"
                      onClick={handleGenerateAts}
                      className="px-3 py-1.5 rounded-lg bg-slate-900 text-white text-xs font-semibold"
                    >
                      Gerar versão ATS
                    </button>
                  </div>

                  {selected.resume_version && (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                      <div className="font-semibold">{selected.resume_version.version_label}</div>
                      <ul className="list-disc pl-4 text-slate-600 space-y-0.5">
                        {selected.resume_version.changes_summary_json.map((c, idx) => (
                          <li key={idx}>{c}</li>
                        ))}
                      </ul>
                      <div className="pt-2 flex flex-wrap gap-2">
                        {selected.resume_version.pdf_path && (
                          <button
                            type="button"
                            onClick={() =>
                              handleDownloadPdf(
                                selected.resume_version!.id,
                                selected.resume_version!.pdf_path
                              )
                            }
                            className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-700"
                          >
                            Baixar PDF
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() =>
                            handleDownloadDocx(
                              selected.resume_version!.id,
                              selected.resume_version!.docx_path
                            )
                          }
                          className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white font-semibold"
                        >
                          Baixar DOCX
                        </button>
                        {!selected.resume_version.approved_by_user ? (
                          <button
                            type="button"
                            onClick={handleApproveAts}
                            className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white font-semibold"
                          >
                            Aprovar currículo ATS
                          </button>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                            <CheckCircle2 className="h-4 w-4" /> Currículo aprovado
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Questions Section */}
                <div className="border-t border-slate-100 pt-4 space-y-3">
                  <h3 className="text-sm font-bold">2. Perguntas do Formulário de Recrutamento</h3>
                  <form onSubmit={handleAddQuestion} className="space-y-2">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={questionText}
                        onChange={(e) => setQuestionText(e.target.value)}
                        placeholder="Cole uma pergunta do formulário (ex.: mensagem para recrutador, experiência...)"
                        className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-xs"
                      />
                      <button
                        type="submit"
                        className="px-3 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold"
                      >
                        Preparar
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <select
                        value={fieldType}
                        onChange={(e) => setFieldType(e.target.value)}
                        className="rounded-lg border border-slate-300 px-2.5 py-1 text-[11px] text-slate-700"
                      >
                        <option value="texto_longo">Texto discursivo</option>
                        <option value="texto_curto">Texto curto</option>
                        <option value="objetiva">Objetiva (Sim/Não/Número)</option>
                        <option value="selecao">Seleção de alternativa</option>
                      </select>
                      <input
                        type="number"
                        min={10}
                        max={10000}
                        value={maxChars}
                        onChange={(e) => setMaxChars(e.target.value)}
                        placeholder="Limite de caracteres (opcional)"
                        className="w-48 rounded-lg border border-slate-300 px-2.5 py-1 text-[11px]"
                      />
                    </div>
                  </form>

                  <div className="space-y-3">
                    {selected.answers.map((ans) => (
                      <div
                        key={ans.id}
                        className="p-3 rounded-xl border border-slate-200 space-y-2 text-xs"
                      >
                        <div className="font-semibold text-slate-900">{ans.question_text}</div>
                        <div className="text-[11px] text-slate-500">
                          Categoria: <strong>{ans.question_category}</strong>
                          {ans.requires_human_input && !ans.approved_answer && (
                            <span className="ml-2 text-amber-700 font-semibold">
                              · Exige sua resposta/decisão
                            </span>
                          )}
                        </div>
                        {ans.evidence_refs_json.length > 0 && (
                          <div className="text-[11px] text-indigo-700 bg-indigo-50/70 px-2.5 py-1.5 rounded-lg">
                            {ans.evidence_refs_json.join(" · ")}
                          </div>
                        )}
                        <textarea
                          rows={2}
                          value={answerDrafts[ans.id] || ""}
                          onChange={(e) =>
                            setAnswerDrafts({ ...answerDrafts, [ans.id]: e.target.value })
                          }
                          placeholder="Digite ou revise sua resposta..."
                          className="w-full rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs"
                        />
                        <button
                          type="button"
                          onClick={() => handleSaveAnswer(ans.id)}
                          className="px-3 py-1 rounded-lg bg-slate-900 text-white font-semibold"
                        >
                          Salvar resposta
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Approval & Submission */}
                <div className="border-t border-slate-100 pt-4 space-y-3">
                  <h3 className="text-sm font-bold flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-indigo-600" />
                    3. Aprovação Humana & Confirmação de Envio
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={selected.has_valid_approval}
                      onClick={handleApproveApplication}
                      className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold disabled:opacity-45"
                    >
                      {selected.has_valid_approval ? "Candidatura aprovada" : "Aprovar candidatura"}
                    </button>
                    <button
                      type="button"
                      disabled={!selected.has_valid_approval || selected.operational_status === "enviada_confirmada"}
                      onClick={() => handleConfirmSubmission(false)}
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-semibold disabled:opacity-45"
                    >
                      <Send className="h-3.5 w-3.5" />
                      {selected.operational_status === "enviada_confirmada"
                        ? "Envio confirmado"
                        : "Confirmar envio realizado"}
                    </button>
                    <button
                      type="button"
                      disabled={
                        !selected.has_valid_approval ||
                        selected.operational_status === "pendente_confirmacao" ||
                        selected.operational_status === "enviada_confirmada"
                      }
                      onClick={() => handleConfirmSubmission(true)}
                      className="px-4 py-2 rounded-xl border border-amber-300 bg-amber-50 text-amber-800 text-xs font-semibold disabled:opacity-45"
                    >
                      Pendente
                    </button>
                  </div>
                </div>

                {/* Interviews */}
                <div className="border-t border-slate-100 pt-4 space-y-3">
                  <h3 className="text-sm font-bold">4. Entrevistas & Histórico</h3>
                  <form onSubmit={handleAddInterview} className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <input
                      type="text"
                      value={ivStage}
                      onChange={(e) => setIvStage(e.target.value)}
                      placeholder="Etapa (ex.: Entrevista RH)"
                      className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs"
                    />
                    <input
                      type="datetime-local"
                      value={ivDate}
                      onChange={(e) => setIvDate(e.target.value)}
                      className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs"
                    />
                    <button
                      type="submit"
                      className="rounded-lg bg-slate-900 text-white text-xs font-semibold px-3 py-1.5"
                    >
                      Agendar entrevista
                    </button>
                  </form>
                  {selected.events.length > 0 && (
                    <ul className="text-[11px] text-slate-500 space-y-1">
                      {selected.events.slice(0, 5).map((ev) => {
                        const eventLabels: Record<string, string> = {
                          human_approved: "Candidatura aprovada",
                          submission_confirmed: "Envio confirmado",
                          submission_ambiguous: "Pendente de confirmação",
                          application_created: "Candidatura criada",
                          resume_tailored: "Currículo ATS gerado",
                          interview_scheduled: "Entrevista agendada",
                          status_changed: "Status atualizado",
                        };
                        const label = eventLabels[ev.event_type] || ev.event_type.replace(/_/g, " ");
                        return (
                          <li key={ev.id}>
                            • <strong>{label}</strong>: {ev.description}
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

export default function CandidaturasPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-50" />}>
      <CandidaturasContent />
    </Suspense>
  );
}

"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, FileUp, Pencil, Plus, Trash2 } from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, Experience, Skill, UserProfile } from "@/lib/api";

export default function ProfilePage() {
  const [profile, setProfile] = useState<Partial<UserProfile>>({});
  const [experiences, setExperiences] = useState<Experience[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [newSkill, setNewSkill] = useState("");
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [editingExpId, setEditingExpId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<Partial<Experience>>({});
  const [hasEditedExp, setHasEditedExp] = useState(false);
  const [adjustedConfirmed, setAdjustedConfirmed] = useState<boolean | null>(null);
  const [linkedinDiff, setLinkedinDiff] = useState<{
    matched_count: number;
    divergences: Array<{ company_name: string; role_title: string | null; cv_period: string; linkedin_period: string; message: string }>;
  } | null>(null);
  const [atsSug, setAtsSug] = useState<{
    ats_readiness_score: number;
    strengths: string[];
    suggestions: string[];
  } | null>(null);

  useEffect(() => {
    Promise.all([
      api.getProfile(),
      api.listExperiences(),
      api.listSkills(),
      api.getAtsSuggestions(),
    ]).then(([prof, exps, sks, sug]) => {
      setProfile(prof);
      setExperiences(exps);
      setSkills(sks);
      setAtsSug(sug);
    });
  }, []);

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    const updated = await api.updateProfile(profile);
    setProfile(updated);
    setSavedMsg("Perfil atualizado com sucesso.");
    setTimeout(() => setSavedMsg(null), 3000);
  }

  async function validateExp(id: string) {
    const updated = await api.updateExperience(id, { validation_status: "verified" });
    setExperiences((prev) => prev.map((x) => (x.id === id ? updated : x)));
  }

  function startEditExp(exp: Experience) {
    setEditingExpId(exp.id);
    setEditDraft({
      company_name: exp.company_name,
      role_title: exp.role_title,
      raw_period_text: exp.raw_period_text || "",
      sector: exp.sector || "",
      responsibilities: exp.responsibilities || "",
      proven_results: exp.proven_results || "",
    });
  }

  async function saveEditExp(id: string) {
    const updated = await api.updateExperience(id, {
      ...editDraft,
      validation_status: "corrected",
    });
    setExperiences((prev) => prev.map((x) => (x.id === id ? updated : x)));
    setEditingExpId(null);
    setHasEditedExp(true);
    setAdjustedConfirmed(null);
    setAtsSug(await api.getAtsSuggestions());
  }

  async function handleLinkedinCompare(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const diff = await api.compareWithLinkedin(file);
    setLinkedinDiff(diff);
  }

  async function handleUseAdjustedCv(useAdjusted: boolean) {
    if (!useAdjusted) {
      setAdjustedConfirmed(false);
      return;
    }
    await api.buildAdjustedResume(true);
    setAdjustedConfirmed(true);
    setSavedMsg("CV ajustado gerado e definido como principal na plataforma!");
  }

  async function deleteExp(id: string) {
    await api.deleteExperience(id);
    setExperiences((prev) => prev.filter((x) => x.id !== id));
    setHasEditedExp(true);
  }

  async function addSkill(e: React.FormEvent) {
    e.preventDefault();
    if (!newSkill.trim()) return;
    const created = await api.createSkill({
      name: newSkill.trim(),
      validation_status: "verified",
      origin: "manual",
    });
    setSkills((prev) => [created, ...prev]);
    setNewSkill("");
  }

  async function deleteSkill(id: string) {
    await api.deleteSkill(id);
    setSkills((prev) => prev.filter((x) => x.id !== id));
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Meu Perfil · Verified Professional Profile</h1>
          <p className="text-sm text-slate-600">
            Todas as informações possuem origem, evidência e situação de validação.
          </p>
        </div>

        {savedMsg && (
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-sm text-emerald-700">
            {savedMsg}
          </div>
        )}

        <form
          onSubmit={saveProfile}
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4"
        >
          <h2 className="text-base font-bold">Dados Profissionais</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Headline profissional"
              value={profile.headline || ""}
              onChange={(e) => setProfile({ ...profile, headline: e.target.value })}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              type="text"
              placeholder="Senioridade (ex.: Sênior, Gerência)"
              value={profile.seniority_level || ""}
              onChange={(e) => setProfile({ ...profile, seniority_level: e.target.value })}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              type="text"
              placeholder="Cidade"
              value={profile.city || ""}
              onChange={(e) => setProfile({ ...profile, city: e.target.value })}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              type="text"
              placeholder="Estado (UF)"
              value={profile.state || ""}
              onChange={(e) => setProfile({ ...profile, state: e.target.value })}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <textarea
            rows={3}
            placeholder="Resumo profissional"
            value={profile.summary || ""}
            onChange={(e) => setProfile({ ...profile, summary: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700"
          >
            Salvar alterações
          </button>
        </form>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-base font-bold">Experiências Profissionais ({experiences.length})</h2>
          {experiences.length === 0 ? (
            <p className="text-sm text-slate-500">
              Nenhuma experiência registrada. Importe seu currículo em Currículos.
            </p>
          ) : (
            <div className="space-y-3">
              {experiences.map((exp) => (
                <div
                  key={exp.id}
                  className="p-4 rounded-xl border border-slate-200 space-y-3"
                >
                  {editingExpId === exp.id ? (
                    <div className="space-y-2">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <input
                          type="text"
                          value={editDraft.role_title || ""}
                          onChange={(e) => setEditDraft({ ...editDraft, role_title: e.target.value })}
                          placeholder="Cargo"
                          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs"
                        />
                        <input
                          type="text"
                          value={editDraft.company_name || ""}
                          onChange={(e) => setEditDraft({ ...editDraft, company_name: e.target.value })}
                          placeholder="Empresa"
                          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs"
                        />
                        <input
                          type="text"
                          value={editDraft.raw_period_text || ""}
                          onChange={(e) => setEditDraft({ ...editDraft, raw_period_text: e.target.value })}
                          placeholder="Período (ex.: Abr/2018 – Mai/2023)"
                          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs"
                        />
                        <input
                          type="text"
                          value={editDraft.sector || ""}
                          onChange={(e) => setEditDraft({ ...editDraft, sector: e.target.value })}
                          placeholder="Setor"
                          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs"
                        />
                      </div>
                      <textarea
                        rows={2}
                        value={editDraft.responsibilities || ""}
                        onChange={(e) => setEditDraft({ ...editDraft, responsibilities: e.target.value })}
                        placeholder="Responsabilidades"
                        className="w-full rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs"
                      />
                      <input
                        type="text"
                        value={editDraft.proven_results || ""}
                        onChange={(e) => setEditDraft({ ...editDraft, proven_results: e.target.value })}
                        placeholder="Resultados comprovados"
                        className="w-full rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs"
                      />
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => saveEditExp(exp.id)}
                          className="px-3 py-1 rounded-lg bg-indigo-600 text-white text-xs font-semibold"
                        >
                          Salvar edição
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingExpId(null)}
                          className="px-3 py-1 rounded-lg border border-slate-300 text-xs"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="font-semibold text-sm">
                          {exp.role_title} — {exp.company_name}
                          {exp.sector && <span className="text-xs font-normal text-slate-500"> ({exp.sector})</span>}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          Origem: {exp.origin} · Validação:{" "}
                          <span
                            className={
                              exp.validation_status === "verified" || exp.validation_status === "corrected"
                                ? "text-emerald-700 font-semibold"
                                : "text-amber-700 font-semibold"
                            }
                          >
                            {exp.validation_status}
                          </span>
                          {exp.raw_period_text && ` · ${exp.raw_period_text}`}
                        </div>
                        {exp.ambiguity_note && (
                          <p className="text-xs text-amber-700 mt-1">{exp.ambiguity_note}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {exp.validation_status !== "verified" && (
                          <button
                            type="button"
                            onClick={() => validateExp(exp.id)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold"
                          >
                            <CheckCircle2 className="h-3.5 w-3.5" /> Validar
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => startEditExp(exp)}
                          className="p-1.5 text-slate-500 hover:text-indigo-600"
                          title="Editar experiência"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => deleteExp(exp.id)}
                          className="p-1.5 text-slate-400 hover:text-red-600"
                          title="Excluir experiência"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-base font-bold">Competências Verificadas ({skills.length})</h2>
          <form onSubmit={addSkill} className="flex gap-2">
            <input
              type="text"
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              placeholder="Adicionar competência comprovada"
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              type="submit"
              className="inline-flex items-center gap-1 px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-semibold"
            >
              <Plus className="h-4 w-4" /> Adicionar
            </button>
          </form>
          <div className="flex flex-wrap gap-2">
            {skills.map((s) => (
              <span
                key={s.id}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-xs font-medium text-slate-800"
              >
                {s.name}
                <button
                  type="button"
                  onClick={() => deleteSkill(s.id)}
                  className="text-slate-400 hover:text-red-600"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Comparação CV vs LinkedIn + Sugestões ATS + CV Ajustado */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-bold">Comparação de Datas (CV vs. LinkedIn)</h2>
              <p className="text-xs text-slate-500">
                Envie o PDF do LinkedIn para apontar divergências de datas de início e fim.
              </p>
            </div>
            <label className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-300 text-xs font-semibold cursor-pointer hover:bg-slate-50">
              <FileUp className="h-4 w-4 text-indigo-600" />
              Enviar PDF do LinkedIn
              <input type="file" accept=".pdf,.docx" onChange={handleLinkedinCompare} className="hidden" />
            </label>
          </div>
          {linkedinDiff && (
            <div className="space-y-2 text-xs">
              <div className="font-semibold">
                Empresas comparadas: {linkedinDiff.matched_count} · Divergências: {linkedinDiff.divergences.length}
              </div>
              {linkedinDiff.divergences.map((d, i) => (
                <div key={i} className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900">
                  <strong>{d.company_name}</strong>: CV (<strong>{d.cv_period}</strong>) vs LinkedIn (<strong>{d.linkedin_period}</strong>)
                </div>
              ))}
            </div>
          )}
        </div>

        {atsSug && (
          <div className="bg-white p-6 rounded-2xl border border-indigo-200 shadow-sm space-y-2">
            <h2 className="text-base font-bold text-indigo-900">
              Sugestões para Algoritmos de Recrutamento (ATS) · Prontidão: {atsSug.ats_readiness_score}/100
            </h2>
            <ul className="list-disc pl-5 text-xs text-slate-700 space-y-1">
              {atsSug.suggestions.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        )}

        {hasEditedExp && adjustedConfirmed === null && (
          <div className="p-5 rounded-2xl border border-emerald-300 bg-emerald-50 space-y-2">
            <div className="text-sm font-bold text-emerald-900">
              Você editou informações do perfil extraído
            </div>
            <p className="text-xs text-emerald-800">
              Deseja gerar este CV ajustado e utilizá-lo dentro da plataforma no lugar do arquivo original enviado?
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <button
                type="button"
                onClick={() => handleUseAdjustedCv(true)}
                className="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700"
              >
                Sim, usar CV ajustado na plataforma
              </button>
              <button
                type="button"
                onClick={() => handleUseAdjustedCv(false)}
                className="px-4 py-2 rounded-xl bg-white border border-slate-300 text-xs font-semibold text-slate-700"
              >
                Não, manter arquivo original
              </button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

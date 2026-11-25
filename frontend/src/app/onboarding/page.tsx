"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  FileUp,
  Pencil,
  Plus,
  ShieldCheck,
  Sparkles,
  Trash2,
} from "lucide-react";
import {
  api,
  ApiError,
  CareerPreference,
  Experience,
  FavoriteCompany,
  getToken,
  ResumeItem,
  Skill,
  TargetRole,
  TargetRoleSuggestion,
  UserProfile,
} from "@/lib/api";

const STEPS = [
  "Conta e Perfil",
  "Currículo e Validação",
  "Cargos-Alvo",
  "Empresas Preferidas",
  "Preferências",
  "Agentes",
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Step 1
  const [profile, setProfile] = useState<Partial<UserProfile>>({});
  // Step 2
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [experiences, setExperiences] = useState<Experience[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [editingExpId, setEditingExpId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<Partial<Experience>>({});
  const [hasEditedExp, setHasEditedExp] = useState(false);
  const [adjustedConfirmed, setAdjustedConfirmed] = useState<boolean | null>(null);
  const [linkedinDiff, setLinkedinDiff] = useState<{
    matched_count: number;
    divergences: Array<{ company_name: string; role_title: string | null; cv_period: string; linkedin_period: string; message: string }>;
    only_in_cv: Array<{ company_name: string; role_title: string | null; period: string | null }>;
    only_in_linkedin: Array<{ company_name: string; role_title: string | null; period: string | null }>;
  } | null>(null);
  const [atsSug, setAtsSug] = useState<{
    ats_readiness_score: number;
    strengths: string[];
    suggestions: string[];
    actionable_options?: {
      suggested_skills: Array<{ name: string; evidence: string }>;
      suggested_summary: { text: string; evidence: string } | null;
    };
  } | null>(null);
  const [previewData, setPreviewData] = useState<{
    content: {
      full_name: string;
      email: string;
      phone?: string | null;
      city?: string | null;
      state?: string | null;
      location?: string;
      linkedin_url?: string | null;
      summary?: string;
      skills: string[];
      experiences: Array<{
        company_name: string;
        role_title: string;
        sector?: string | null;
        raw_period_text?: string | null;
        responsibilities?: string | null;
        responsibilities_list?: string[];
        proven_results?: string | null;
      }>;
      education?: Array<{ raw?: string }>;
      languages?: Array<{ raw?: string }>;
    };
    changes_summary: string[];
  } | null>(null);
  const [adjustedResumeId, setAdjustedResumeId] = useState<string | null>(null);
  const [editingPreview, setEditingPreview] = useState(false);
  const [cvContactDraft, setCvContactDraft] = useState<{
    contact_email: string;
    phone: string;
    city: string;
    state: string;
    linkedin_url: string;
    summary: string;
  }>({ contact_email: "", phone: "", city: "", state: "", linkedin_url: "", summary: "" });
  // Step 3
  const [roles, setRoles] = useState<TargetRole[]>([]);
  const [suggestions, setSuggestions] = useState<TargetRoleSuggestion[]>([]);
  const [newRoleTitle, setNewRoleTitle] = useState("");
  const [newRoleSeniority, setNewRoleSeniority] = useState("Sênior");
  const [newRolePriority, setNewRolePriority] = useState<"alta" | "media" | "baixa">("alta");
  const [newRoleMinSalary, setNewRoleMinSalary] = useState("");
  const [newRoleMaxSalary, setNewRoleMaxSalary] = useState("");
  // Step 4
  const [companies, setCompanies] = useState<FavoriteCompany[]>([]);
  const [newCompName, setNewCompName] = useState("");
  const [newCompCareers, setNewCompCareers] = useState("");
  const [newCompCity, setNewCompCity] = useState("");
  const [newCompState, setNewCompState] = useState("");
  const [newCompSector, setNewCompSector] = useState("");
  const [newCompPriority, setNewCompPriority] = useState<"alta" | "media" | "baixa">("alta");
  const [segmentInput, setSegmentInput] = useState("");
  const [segmentCompanies, setSegmentCompanies] = useState<
    Array<{
      id: string;
      name: string;
      careers_page_url: string | null;
      city: string | null;
      state: string | null;
      sector: string | null;
    }>
  >([]);
  const [companySuggestions, setCompanySuggestions] = useState<
    Array<{
      id: string;
      name: string;
      official_website: string | null;
      careers_page_url: string | null;
      city: string | null;
      state: string | null;
      sector: string | null;
    }>
  >([]);
  // Step 5 & 6
  const [prefs, setPrefs] = useState<Partial<CareerPreference>>({
    work_modalities: ["remoto", "hibrido"],
    search_frequency_hours: 24,
    max_recommended_jobs: 20,
    min_match_score: 65,
    prioritize_favorite_companies: true,
    application_mode: "supervised",
  });

  useEffect(() => {
    if (!getToken()) {
      router.replace("/auth?mode=login");
      return;
    }
    Promise.all([
      api.me(),
      api.getProfile(),
      api.listResumes(),
      api.listExperiences(),
      api.listSkills(),
      api.listTargetRoles(),
      api.listFavoriteCompanies(),
      api.getPreferences(),
    ])
      .then(([me, prof, resList, expList, skillList, roleList, compList, prefData]) => {
        setStep(me.onboarding_step || 1);
        setProfile(prof);
        setResumes(resList);
        setExperiences(expList);
        setSkills(skillList);
        setRoles(roleList);
        setCompanies(compList);
        setPrefs(prefData);
      })
      .catch(() => router.replace("/auth?mode=login"))
      .finally(() => setLoading(false));
  }, [router]);

  async function goToStep(nextStep: number, completed?: boolean) {
    setError(null);
    setSuccessMsg(null);
    await api.updateOnboarding(nextStep, completed);
    if (completed) {
      router.push("/app");
    } else {
      setStep(nextStep);
    }
  }

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateProfile(profile);
      setProfile(updated);
      await goToStep(2);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao salvar perfil.");
    } finally {
      setSaving(false);
    }
  }

  async function handleResumeUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setSaving(true);
    setError(null);
    try {
      const uploaded = await api.uploadResume(file);
      const [resList, expList, skillList] = await Promise.all([
        api.listResumes(),
        api.listExperiences(),
        api.listSkills(),
      ]);
      setResumes(resList);
      setExperiences(expList);
      setSkills(skillList);
      setHasEditedExp(false);
      setAdjustedConfirmed(null);
      setSuccessMsg(`Currículo "${uploaded.original_filename}" processado! Revise e valide as informações extraídas abaixo.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao importar currículo.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteResume(id: string) {
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await api.deleteResume(id);
      const [resList, expList, skillList] = await Promise.all([
        api.listResumes(),
        api.listExperiences(),
        api.listSkills(),
      ]);
      setResumes(resList);
      setExperiences(expList);
      setSkills(skillList);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao excluir currículo.");
    } finally {
      setSaving(false);
    }
  }

  async function validateExperience(id: string) {
    const updated = await api.updateExperience(id, { validation_status: "verified" });
    setExperiences((prev) => prev.map((x) => (x.id === id ? updated : x)));
  }

  function startEditExperience(exp: Experience) {
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

  async function saveEditExperience(id: string) {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateExperience(id, {
        ...editDraft,
        validation_status: "corrected",
      });
      setExperiences((prev) => prev.map((x) => (x.id === id ? updated : x)));
      setEditingExpId(null);
      setHasEditedExp(true);
      setAdjustedConfirmed(null);
      const sug = await api.getAtsSuggestions();
      setAtsSug(sug);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao editar experiência.");
    } finally {
      setSaving(false);
    }
  }

  async function handleLinkedinCompare(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setSaving(true);
    setError(null);
    try {
      const diff = await api.compareWithLinkedin(file);
      setLinkedinDiff(diff);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao comparar com LinkedIn.");
    } finally {
      setSaving(false);
    }
  }

  async function handleUseAdjustedCv(useAdjusted: boolean) {
    if (!useAdjusted) {
      setAdjustedConfirmed(false);
      return;
    }
    setSaving(true);
    try {
      const created = await api.buildAdjustedResume(true);
      const resList = await api.listResumes();
      setResumes(resList);
      setAdjustedResumeId(created.id);
      setAdjustedConfirmed(true);
      setSuccessMsg("CV ajustado gerado e definido como principal na plataforma!");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao gerar CV ajustado.");
    } finally {
      setSaving(false);
    }
  }

  async function handlePreviewAdjusted() {
    setError(null);
    try {
      const prev = await api.previewAdjustedResume();
      setPreviewData(prev);
      setCvContactDraft({
        contact_email: prev.content.email || "",
        phone: prev.content.phone || "",
        city: prev.content.city || "",
        state: prev.content.state || "",
        linkedin_url: prev.content.linkedin_url || "",
        summary: prev.content.summary || "",
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao gerar prévia do CV ajustado.");
    }
  }

  async function handleSavePreviewEdits() {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateProfile({
        contact_email: cvContactDraft.contact_email.trim() || null,
        phone: cvContactDraft.phone.trim() || null,
        city: cvContactDraft.city.trim() || null,
        state: cvContactDraft.state.trim() || null,
        linkedin_url: cvContactDraft.linkedin_url.trim() || null,
        summary: cvContactDraft.summary.trim() || null,
      });
      setProfile(updated);
      setAdjustedResumeId(null);
      setEditingPreview(false);
      await handlePreviewAdjusted();
      setSuccessMsg("Alterações do CV salvas! A prévia e o arquivo DOCX foram atualizados.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao salvar alterações do CV.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDownloadAdjustedCv() {
    setError(null);
    try {
      let targetId = adjustedResumeId;
      if (!targetId) {
        const created = await api.buildAdjustedResume(false);
        targetId = created.id;
        setAdjustedResumeId(created.id);
      }
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${apiBase}/resumes/${targetId}/download`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("Falha ao baixar arquivo.");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "CV_Ajustado.docx";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Erro ao baixar o CV ajustado.");
    }
  }

  async function handleIncludeSuggestedSkill(name: string) {
    await api.createSkill({
      name,
      origin: "ats_suggestion_from_cv",
      validation_status: "verified",
    });
    setSkills(await api.listSkills());
    setHasEditedExp(true);
    setAdjustedConfirmed(null);
    setAtsSug(await api.getAtsSuggestions());
  }

  async function handleIncludeAllSuggestions() {
    const sugSkills = atsSug?.actionable_options?.suggested_skills || [];
    for (const s of sugSkills) {
      await api.createSkill({
        name: s.name,
        origin: "ats_suggestion_from_cv",
        validation_status: "verified",
      });
    }
    if (atsSug?.actionable_options?.suggested_summary?.text) {
      const updatedProf = await api.updateProfile({
        summary: atsSug.actionable_options.suggested_summary.text,
      });
      setProfile(updatedProf);
    }
    setSkills(await api.listSkills());
    setHasEditedExp(true);
    setAdjustedConfirmed(null);
    setAtsSug(await api.getAtsSuggestions());
  }

  async function loadAtsSuggestions() {
    const sug = await api.getAtsSuggestions();
    setAtsSug(sug);
  }

  async function removeExperience(id: string) {
    await api.deleteExperience(id);
    setExperiences((prev) => prev.filter((x) => x.id !== id));
    setHasEditedExp(true);
  }

  async function handleAddRole(titleParam?: string) {
    const title = (titleParam ?? newRoleTitle).trim();
    if (!title) return;
    setSaving(true);
    setError(null);
    try {
      const created = await api.createTargetRole({
        title,
        desired_seniority: newRoleSeniority,
        priority: newRolePriority,
        min_salary_brl: !titleParam && newRoleMinSalary ? Number(newRoleMinSalary) : null,
        desired_salary_brl: !titleParam && newRoleMaxSalary ? Number(newRoleMaxSalary) : null,
        status: "ativo",
      });
      setRoles((prev) => [created, ...prev]);
      if (!titleParam) {
        setNewRoleTitle("");
        setNewRoleMinSalary("");
        setNewRoleMaxSalary("");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao adicionar cargo.");
    } finally {
      setSaving(false);
    }
  }

  async function loadSuggestions() {
    const s = await api.getRoleSuggestions();
    setSuggestions(s);
  }

  async function handleCompanySearch(val: string, sec: string) {
    setNewCompName(val);
    setNewCompSector(sec);
    if (val.trim().length >= 2 || sec.trim().length > 0) {
      try {
        const list = await api.searchCompanyCatalog(val.trim(), sec.trim());
        setCompanySuggestions(list);
      } catch {
        setCompanySuggestions([]);
      }
    } else {
      setCompanySuggestions([]);
    }
  }

  function selectCompanySuggestion(item: {
    name: string;
    careers_page_url: string | null;
    city: string | null;
    state: string | null;
    sector: string | null;
  }) {
    setNewCompName(item.name);
    setNewCompCareers(item.careers_page_url || "");
    setNewCompCity(item.city || "");
    setNewCompState(item.state || "");
    setNewCompSector(item.sector || "");
    setCompanySuggestions([]);
  }

  async function handleAddCompany(e: React.FormEvent) {
    e.preventDefault();
    if (!newCompName.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const created = await api.addFavoriteCompany({
        name: newCompName.trim(),
        careers_page_url: newCompCareers.trim() || undefined,
        city: newCompCity.trim() || undefined,
        state: newCompState.trim() || undefined,
        sector: newCompSector.trim() || undefined,
        priority: newCompPriority,
      });
      setCompanies((prev) => [created, ...prev]);
      setNewCompName("");
      setNewCompCareers("");
      setNewCompCity("");
      setNewCompState("");
      setNewCompSector("");
      setCompanySuggestions([]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao cadastrar empresa.");
    } finally {
      setSaving(false);
    }
  }

  async function handleCsvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setSaving(true);
    setError(null);
    try {
      const res = await api.importCompaniesCsv(file);
      const list = await api.listFavoriteCompanies();
      setCompanies(list);
      setSuccessMsg(`${res.imported_count} empresa(s) importada(s) via CSV.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao importar CSV.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSavePreferences(nextStep: number, complete = false) {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updatePreferences(prefs);
      setPrefs(updated);
      await goToStep(nextStep, complete);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao salvar preferências.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-sm text-slate-600">
        Preparando seu onboarding...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2 font-bold text-slate-900">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
              <Sparkles className="h-4 w-4" />
            </span>
            Onboarding · Career Hunter AI
          </div>
          <button
            type="button"
            onClick={() => router.push("/app")}
            className="text-xs font-medium text-slate-500 hover:text-slate-900"
          >
            Ir para o painel
          </button>
        </div>

        {/* Stepper */}
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 mb-8">
          {STEPS.map((label, idx) => {
            const num = idx + 1;
            const active = step === num;
            const done = step > num;
            return (
              <button
                key={label}
                type="button"
                onClick={() => setStep(num)}
                className={`p-2.5 rounded-xl border text-left transition ${
                  active
                    ? "border-indigo-600 bg-indigo-50 text-indigo-800"
                    : done
                    ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                    : "border-slate-200 bg-white text-slate-500"
                }`}
              >
                <div className="text-[11px] font-bold">Etapa {num}</div>
                <div className="text-xs font-medium truncate">{label}</div>
              </button>
            );
          })}
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">
            {error}
          </div>
        )}
        {successMsg && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-sm text-emerald-700">
            {successMsg}
          </div>
        )}

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
          {/* ETAPA 1 */}
          {step === 1 && (
            <form onSubmit={handleSaveProfile} className="space-y-4">
              <h1 className="text-xl font-bold">Etapa 1 — Conta e Perfil Profissional</h1>
              <p className="text-sm text-slate-600">
                Informe seus dados básicos. Você poderá completar ou editar depois.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Título / Headline</label>
                  <input
                    type="text"
                    value={profile.headline || ""}
                    onChange={(e) => setProfile({ ...profile, headline: e.target.value })}
                    placeholder="Ex.: Gerente de Produto Sênior"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Senioridade atual</label>
                  <select
                    value={profile.seniority_level || ""}
                    onChange={(e) => setProfile({ ...profile, seniority_level: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="">Selecione...</option>
                    <option value="Analista">Analista</option>
                    <option value="Pleno">Pleno</option>
                    <option value="Sênior">Sênior</option>
                    <option value="Especialista">Especialista</option>
                    <option value="Coordenação">Coordenação</option>
                    <option value="Gerência">Gerência</option>
                    <option value="Diretoria">Diretoria</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Cidade</label>
                  <input
                    type="text"
                    value={profile.city || ""}
                    onChange={(e) => setProfile({ ...profile, city: e.target.value })}
                    placeholder="São Paulo"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Estado (UF)</label>
                  <input
                    type="text"
                    value={profile.state || ""}
                    onChange={(e) => setProfile({ ...profile, state: e.target.value })}
                    placeholder="SP"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">LinkedIn</label>
                <input
                  type="url"
                  value={profile.linkedin_url || ""}
                  onChange={(e) => setProfile({ ...profile, linkedin_url: e.target.value })}
                  placeholder="https://linkedin.com/in/seu-perfil"
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div className="pt-4 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700"
                >
                  Salvar e avançar <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </form>
          )}

          {/* ETAPA 2 */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h1 className="text-xl font-bold">Etapa 2 — Importação do Currículo</h1>
                <p className="text-sm text-slate-600">
                  Envie seu currículo em PDF ou DOCX. Extraímos os dados para o{" "}
                  <strong>Verified Professional Profile</strong> e sinalizamos qualquer ambiguidade.
                </p>
              </div>

              {resumes.length === 0 ? (
                <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-300 rounded-xl p-6 cursor-pointer hover:border-indigo-500 transition">
                  <FileUp className="h-8 w-8 text-indigo-600 mb-2" />
                  <span className="text-sm font-semibold text-slate-700">
                    {saving ? "Processando documento..." : "Clique para selecionar PDF ou DOCX"}
                  </span>
                  <span className="text-xs text-slate-500 mt-1">Tamanho máximo: 10 MB</span>
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleResumeUpload}
                    className="hidden"
                  />
                </label>
              ) : (
                <div className="space-y-2">
                  {resumes.length > 1 && (
                    <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 shrink-0" />
                      <span>
                        Existem <strong>{resumes.length} currículos</strong> na sua base. Exclua os
                        antigos para manter apenas o currículo desejado.
                      </span>
                    </div>
                  )}
                  {resumes.map((r) => (
                    <div
                      key={r.id}
                      className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/40 flex items-center justify-between gap-3"
                    >
                      <div>
                        <div className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                          <span>CV anexado: {r.original_filename}</span>
                          {r.is_primary && (
                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-600 text-white">
                              Principal
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5 uppercase">
                          {r.file_format} · {(r.file_size_bytes / 1024).toFixed(1)} KB
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDeleteResume(r.id)}
                        className="p-2 rounded-lg text-slate-500 hover:text-red-600 hover:bg-red-50 transition"
                        title="Excluir CV para enviar outro"
                        aria-label="Excluir CV"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {resumes.length > 0 && resumes[0].ambiguities_json.length > 0 && (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-2">
                  <div className="flex items-center gap-2 text-sm font-semibold text-amber-800">
                    <AlertTriangle className="h-4 w-4" />
                    Ambiguidades sinalizadas para sua revisão
                  </div>
                  <ul className="text-xs text-amber-800 space-y-1 list-disc pl-5">
                    {resumes[0].ambiguities_json.map((amb, i) => (
                      <li key={i}>
                        <strong>{amb.field}:</strong> {amb.message}{" "}
                        {amb.excerpt && <span className="italic">({amb.excerpt})</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div>
                <h2 className="text-sm font-bold text-slate-800 mb-2">
                  Experiências Extraídas ({experiences.length})
                </h2>
                {experiences.length === 0 ? (
                  <p className="text-sm text-slate-500">Nenhuma experiência cadastrada ainda.</p>
                ) : (
                  <div className="space-y-2">
                    {experiences.map((exp) => (
                      <div
                        key={exp.id}
                        className="p-3 rounded-xl border border-slate-200 space-y-3"
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
                              placeholder="Resultados comprovados (opcional)"
                              className="w-full rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs"
                            />
                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={() => saveEditExperience(exp.id)}
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
                                {exp.role_title} · {exp.company_name}
                                {exp.sector && <span className="text-xs font-normal text-slate-500"> ({exp.sector})</span>}
                              </div>
                              <div className="text-xs text-slate-500">
                                Origem: {exp.origin} · Status:{" "}
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
                            </div>
                            <div className="flex items-center gap-2">
                              {exp.validation_status !== "verified" && (
                                <button
                                  type="button"
                                  onClick={() => validateExperience(exp.id)}
                                  className="px-3 py-1 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700"
                                >
                                  Validar
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() => startEditExperience(exp)}
                                className="p-1.5 text-slate-500 hover:text-indigo-600"
                                aria-label="Editar experiência"
                                title="Editar experiência"
                              >
                                <Pencil className="h-4 w-4" />
                              </button>
                              <button
                                type="button"
                                onClick={() => removeExperience(exp.id)}
                                className="p-1.5 text-slate-400 hover:text-red-600"
                                aria-label="Excluir experiência"
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

              {skills.length > 0 && (
                <div>
                  <h2 className="text-sm font-bold text-slate-800 mb-2">
                    Competências Identificadas ({skills.length})
                  </h2>
                  <div className="flex flex-wrap gap-1.5">
                    {skills.map((s) => (
                      <span
                        key={s.id}
                        className="px-2.5 py-1 rounded-full bg-slate-100 text-xs font-medium text-slate-700"
                      >
                        {s.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Comparação de datas CV vs LinkedIn */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="text-xs font-bold text-slate-800">
                      Comparar datas de início/fim com PDF do LinkedIn
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Aponta divergências de períodos entre seu currículo e o perfil exportado do LinkedIn.
                    </div>
                  </div>
                  <label className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-xs font-semibold cursor-pointer hover:bg-slate-100 shrink-0">
                    <FileUp className="h-3.5 w-3.5 text-indigo-600" />
                    Enviar PDF do LinkedIn
                    <input type="file" accept=".pdf,.docx" onChange={handleLinkedinCompare} className="hidden" />
                  </label>
                </div>

                {linkedinDiff && (
                  <div className="space-y-2 text-xs">
                    <div className="font-semibold text-slate-700">
                      Empresas comparadas: {linkedinDiff.matched_count} · Divergências de data: {linkedinDiff.divergences.length}
                    </div>
                    {linkedinDiff.divergences.map((d, i) => (
                      <div key={i} className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900">
                        <strong>{d.company_name}</strong> ({d.role_title}): CV: <strong>{d.cv_period}</strong> vs LinkedIn: <strong>{d.linkedin_period}</strong>
                      </div>
                    ))}
                    {linkedinDiff.divergences.length === 0 && (
                      <div className="text-emerald-700 font-medium">
                        Nenhuma divergência de datas encontrada entre CV e LinkedIn!
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Sugestões ATS alinhadas aos algoritmos de recrutamento */}
              <div className="p-4 rounded-xl border border-indigo-100 bg-indigo-50/40 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-bold text-indigo-900">
                    Sugestões de CV para Algoritmos de Recrutamento (ATS)
                  </div>
                  <button
                    type="button"
                    onClick={loadAtsSuggestions}
                    className="text-xs font-semibold text-indigo-600 hover:underline"
                  >
                    Analisar perfil para ATS
                  </button>
                </div>
                {atsSug && (
                  <div className="space-y-3 text-xs">
                    <div className="font-bold text-indigo-800">
                      Prontidão ATS: {atsSug.ats_readiness_score}/100
                    </div>
                    {atsSug.suggestions.length > 0 && (
                      <ul className="list-disc pl-4 text-slate-700 space-y-1">
                        {atsSug.suggestions.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    )}

                    {((atsSug.actionable_options?.suggested_skills?.length || 0) > 0 ||
                      atsSug.actionable_options?.suggested_summary) && (
                      <div className="p-3 rounded-lg bg-white border border-indigo-200 space-y-2.5">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-bold text-slate-800">
                            Opções identificadas no seu CV/LinkedIn para incluir:
                          </span>
                          <button
                            type="button"
                            onClick={handleIncludeAllSuggestions}
                            className="px-2.5 py-1 rounded-lg bg-indigo-600 text-white text-[11px] font-semibold hover:bg-indigo-700 shrink-0"
                          >
                            Incluir todas
                          </button>
                        </div>

                        {(atsSug.actionable_options?.suggested_skills?.length || 0) > 0 && (
                          <div className="flex flex-wrap gap-1.5">
                            {atsSug.actionable_options!.suggested_skills.map((sk) => (
                              <button
                                key={sk.name}
                                type="button"
                                onClick={() => handleIncludeSuggestedSkill(sk.name)}
                                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-800 hover:bg-indigo-100 font-medium"
                                title={sk.evidence}
                              >
                                <Plus className="h-3 w-3" /> {sk.name}
                              </button>
                            ))}
                          </div>
                        )}

                        {atsSug.actionable_options?.suggested_summary && (
                          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
                            <div className="text-[11px] font-semibold text-slate-700">
                              Sugestão de resumo profissional (baseado nas suas experiências):
                            </div>
                            <p className="text-slate-600 italic">
                              &ldquo;{atsSug.actionable_options.suggested_summary.text}&rdquo;
                            </p>
                            <button
                              type="button"
                              onClick={async () => {
                                const updatedProf = await api.updateProfile({
                                  summary: atsSug.actionable_options!.suggested_summary!.text,
                                });
                                setProfile(updatedProf);
                                setHasEditedExp(true);
                                setAdjustedConfirmed(null);
                                setAtsSug(await api.getAtsSuggestions());
                              }}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-600 text-white text-[11px] font-semibold"
                            >
                              <Plus className="h-3 w-3" /> Incluir resumo
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Visualização, Edição, Download e Confirmação do CV Ajustado (visível sempre que houver CV na base) */}
              {(hasEditedExp || resumes.length > 0) && (
                <div
                  className={`p-4 rounded-xl border space-y-3 ${
                    hasEditedExp
                      ? "border-emerald-300 bg-emerald-50"
                      : "border-slate-200 bg-slate-50"
                  }`}
                >
                  <div
                    className={`text-sm font-bold ${
                      hasEditedExp ? "text-emerald-900" : "text-slate-900"
                    }`}
                  >
                    {adjustedConfirmed
                      ? "CV ajustado ativo na plataforma"
                      : hasEditedExp
                      ? "Você editou informações do currículo extraído"
                      : "CV na Plataforma — Visualizar, Editar e Baixar"}
                  </div>
                  <p
                    className={`text-xs ${
                      hasEditedExp ? "text-emerald-800" : "text-slate-600"
                    }`}
                  >
                    {adjustedConfirmed
                      ? "O CV ajustado foi definido como principal. Você pode pré-visualizar, editar ou baixar o arquivo DOCX abaixo."
                      : hasEditedExp
                      ? "Pré-visualize, edite ou baixe o CV ajustado antes de confirmar se deseja utilizá-lo dentro da plataforma no lugar do arquivo original."
                      : "Visualize como seu CV está formatado na plataforma, edite e-mail/contato/resumo ou baixe a versão em DOCX."}
                  </p>

                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={handlePreviewAdjusted}
                      className="px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-xs font-semibold text-slate-800 hover:bg-slate-100"
                    >
                      Visualizar / Editar CV
                    </button>
                    <button
                      type="button"
                      onClick={handleDownloadAdjustedCv}
                      className="px-3 py-1.5 rounded-lg bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800"
                    >
                      Baixar CV ajustado (.docx)
                    </button>
                    {adjustedConfirmed === null && (
                      <>
                        <button
                          type="button"
                          onClick={() => handleUseAdjustedCv(true)}
                          className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700"
                        >
                          Sim, usar CV ajustado na plataforma
                        </button>
                        <button
                          type="button"
                          onClick={() => handleUseAdjustedCv(false)}
                          className="px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-100"
                        >
                          Não, manter arquivo original
                        </button>
                      </>
                    )}
                  </div>

                  {previewData && (
                    <div className="mt-3 p-5 rounded-xl bg-white border border-slate-200 text-xs space-y-4 max-h-[520px] overflow-y-auto">
                      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                        <div>
                          <div className="text-base font-bold text-slate-900">
                            {previewData.content.full_name}
                          </div>
                          <div className="text-slate-500 mt-0.5">
                            {[
                              previewData.content.email,
                              previewData.content.phone,
                              previewData.content.location,
                              previewData.content.linkedin_url,
                            ]
                              .filter(Boolean)
                              .join(" | ")}
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => setEditingPreview((v) => !v)}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-300 text-slate-700 font-semibold hover:bg-slate-50 shrink-0"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                          {editingPreview ? "Fechar edição" : "Editar dados do CV"}
                        </button>
                      </div>

                      {editingPreview && (
                        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
                          <div className="font-bold text-slate-800">
                            Editar contato e resumo (e-mail de candidaturas separado do e-mail da conta)
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            <input
                              type="email"
                              value={cvContactDraft.contact_email}
                              onChange={(e) =>
                                setCvContactDraft({ ...cvContactDraft, contact_email: e.target.value })
                              }
                              placeholder="E-mail para vagas (ex.: seu.email@gmail.com)"
                              className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs"
                            />
                            <input
                              type="text"
                              value={cvContactDraft.phone}
                              onChange={(e) =>
                                setCvContactDraft({ ...cvContactDraft, phone: e.target.value })
                              }
                              placeholder="Telefone"
                              className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs"
                            />
                            <input
                              type="text"
                              value={cvContactDraft.city}
                              onChange={(e) =>
                                setCvContactDraft({ ...cvContactDraft, city: e.target.value })
                              }
                              placeholder="Cidade"
                              className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs"
                            />
                            <input
                              type="text"
                              value={cvContactDraft.state}
                              onChange={(e) =>
                                setCvContactDraft({ ...cvContactDraft, state: e.target.value })
                              }
                              placeholder="Estado (UF)"
                              className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs"
                            />
                          </div>
                          <input
                            type="url"
                            value={cvContactDraft.linkedin_url}
                            onChange={(e) =>
                              setCvContactDraft({ ...cvContactDraft, linkedin_url: e.target.value })
                            }
                            placeholder="LinkedIn URL"
                            className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs"
                          />
                          <textarea
                            rows={4}
                            value={cvContactDraft.summary}
                            onChange={(e) =>
                              setCvContactDraft({ ...cvContactDraft, summary: e.target.value })
                            }
                            placeholder="Resumo Profissional"
                            className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs"
                          />
                          <button
                            type="button"
                            onClick={handleSavePreviewEdits}
                            disabled={saving}
                            className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700"
                          >
                            Salvar alterações no CV
                          </button>
                        </div>
                      )}

                      {previewData.content.summary && (
                        <div>
                          <div className="font-bold text-slate-900 uppercase tracking-wide text-[11px] border-b border-slate-100 pb-1">
                            Resumo Profissional
                          </div>
                          <p className="text-slate-700 mt-1.5 whitespace-pre-line leading-relaxed">
                            {previewData.content.summary}
                          </p>
                        </div>
                      )}

                      {previewData.content.skills.length > 0 && (
                        <div>
                          <div className="font-bold text-slate-900 uppercase tracking-wide text-[11px] border-b border-slate-100 pb-1">
                            Competências
                          </div>
                          <div className="flex flex-wrap gap-1.5 mt-1.5">
                            {previewData.content.skills.map((sk) => (
                              <span key={sk} className="px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                                {sk}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <div>
                        <div className="font-bold text-slate-900 uppercase tracking-wide text-[11px] border-b border-slate-100 pb-1">
                          Experiência Profissional
                        </div>
                        <div className="space-y-3 mt-2">
                          {previewData.content.experiences.map((ex, i) => (
                            <div key={i} className="space-y-1">
                              <div className="font-bold text-slate-900">
                                {ex.company_name}
                                {ex.sector ? <span className="font-normal text-slate-500"> — {ex.sector}</span> : null}
                              </div>
                              <div className="font-semibold text-indigo-800">
                                {ex.role_title}
                                {ex.raw_period_text ? <span className="font-normal text-slate-500"> | {ex.raw_period_text}</span> : null}
                              </div>
                              {(ex.responsibilities_list && ex.responsibilities_list.length > 0) ? (
                                <ul className="list-disc pl-4 text-slate-700 space-y-0.5 leading-relaxed">
                                  {ex.responsibilities_list.map((b, bi) => (
                                    <li key={bi}>{b}</li>
                                  ))}
                                </ul>
                              ) : (
                                ex.responsibilities && (
                                  <p className="text-slate-700 whitespace-pre-line">{ex.responsibilities}</p>
                                )
                              )}
                              {ex.proven_results && (
                                <p className="text-emerald-700 font-medium">
                                  Resultados comprovados: {ex.proven_results}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>

                      {previewData.content.education && previewData.content.education.length > 0 && (
                        <div>
                          <div className="font-bold text-slate-900 uppercase tracking-wide text-[11px] border-b border-slate-100 pb-1">
                            Formação Acadêmica
                          </div>
                          <ul className="list-disc pl-4 text-slate-700 mt-1 space-y-0.5">
                            {previewData.content.education.map((ed, i) => (
                              <li key={i}>{ed.raw || String(ed)}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {previewData.content.languages && previewData.content.languages.length > 0 && (
                        <div>
                          <div className="font-bold text-slate-900 uppercase tracking-wide text-[11px] border-b border-slate-100 pb-1">
                            Idiomas
                          </div>
                          <p className="text-slate-700 mt-1">
                            {previewData.content.languages.map((l) => l.raw || String(l)).join(" · ")}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-xs font-bold text-slate-800">
                    Conectar ChatGPT / OpenAI (Opcional — Altamente Recomendado)
                  </div>
                  <a
                    href="https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key"
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] font-semibold text-indigo-600 hover:underline"
                  >
                    Como criar chave na OpenAI
                  </a>
                </div>
                <p className="text-[11px] text-slate-600">
                  Permite adaptar seu currículo ATS em PDF e respostas de recrutamento usando o Agente Especialista Estratégico com seus fatos reais.
                </p>
                <input
                  type="password"
                  value={prefs.openai_api_key || ""}
                  onChange={(e) => setPrefs({ ...prefs, openai_api_key: e.target.value })}
                  placeholder={
                    prefs.has_openai_key
                      ? "Chave OpenAI já conectada (digite outra para substituir)"
                      : "Cole sua chave API OpenAI (sk-...)"
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs"
                />
              </div>

              <div className="pt-4 flex justify-between">
                <button
                  type="button"
                  onClick={() => goToStep(1)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-300 text-sm font-medium"
                >
                  <ArrowLeft className="h-4 w-4" /> Voltar
                </button>
                <button
                  type="button"
                  onClick={() => goToStep(3)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700"
                >
                  Avançar <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* ETAPA 3 */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h1 className="text-xl font-bold">Etapa 3 — Cargos-Alvo</h1>
                <p className="text-sm text-slate-600">
                  Cadastre os cargos que você pretende conquistar. Sugestões da IA exigem sua aprovação explícita.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <input
                  type="text"
                  value={newRoleTitle}
                  onChange={(e) => setNewRoleTitle(e.target.value)}
                  placeholder="Ex.: Gerente de Engenharia"
                  className="sm:col-span-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
                <select
                  value={newRoleSeniority}
                  onChange={(e) => setNewRoleSeniority(e.target.value)}
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="Analista">Analista</option>
                  <option value="Pleno">Pleno</option>
                  <option value="Sênior">Sênior</option>
                  <option value="Especialista">Especialista</option>
                  <option value="Coordenação">Coordenação</option>
                  <option value="Gerência">Gerência</option>
                  <option value="Diretoria">Diretoria</option>
                </select>
                <button
                  type="button"
                  onClick={() => handleAddRole()}
                  disabled={saving}
                  className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-indigo-600 text-white text-sm font-semibold px-4 py-2 hover:bg-indigo-700"
                >
                  <Plus className="h-4 w-4" /> Adicionar
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <input
                  type="number"
                  min={0}
                  value={newRoleMinSalary}
                  onChange={(e) => setNewRoleMinSalary(e.target.value)}
                  placeholder="Pretensão mínima para este cargo (R$ — opcional)"
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
                <input
                  type="number"
                  min={0}
                  value={newRoleMaxSalary}
                  onChange={(e) => setNewRoleMaxSalary(e.target.value)}
                  placeholder="Pretensão máxima para este cargo (R$ — opcional)"
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>

              <div>
                <button
                  type="button"
                  onClick={loadSuggestions}
                  className="text-xs font-semibold text-indigo-600 hover:underline"
                >
                  Ver sugestões fundamentadas no meu currículo
                </button>
                {suggestions.length > 0 && (
                  <div className="mt-2 space-y-2">
                    {suggestions.map((sug, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-xl bg-indigo-50/60 border border-indigo-100 flex items-center justify-between gap-3"
                      >
                        <div>
                          <div className="text-sm font-semibold text-slate-900">{sug.title}</div>
                          <div className="text-xs text-slate-600">{sug.justification}</div>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleAddRole(sug.title)}
                          className="px-3 py-1 rounded-lg bg-indigo-600 text-white text-xs font-semibold shrink-0"
                        >
                          Aprovar e incluir
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                {roles.map((r) => (
                  <div
                    key={r.id}
                    className="p-3 rounded-xl border border-slate-200 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-sm font-semibold">{r.title}</div>
                      <div className="text-xs text-slate-500">
                        {r.desired_seniority || "Senioridade não definida"} · Prioridade {r.priority} · {r.status}
                        {(r.min_salary_brl || r.desired_salary_brl) && (
                          <span className="ml-2 text-indigo-700 font-medium">
                            · Pretensão:{" "}
                            {r.min_salary_brl ? `R$ ${r.min_salary_brl.toLocaleString("pt-BR")}` : "—"}
                            {" a "}
                            {r.desired_salary_brl ? `R$ ${r.desired_salary_brl.toLocaleString("pt-BR")}` : "—"}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-xs font-bold text-slate-800">
                    Conectar ChatGPT / OpenAI (Opcional — Altamente Recomendado)
                  </div>
                  <a
                    href="https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key"
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] font-semibold text-indigo-600 hover:underline"
                  >
                    Como criar chave na OpenAI
                  </a>
                </div>
                <p className="text-[11px] text-slate-600">
                  Permite adaptar seu currículo ATS em PDF e respostas de recrutamento usando o Agente Especialista Estratégico com seus fatos reais.
                </p>
                <input
                  type="password"
                  value={prefs.openai_api_key || ""}
                  onChange={(e) => setPrefs({ ...prefs, openai_api_key: e.target.value })}
                  placeholder={
                    prefs.has_openai_key
                      ? "Chave OpenAI já conectada (digite outra para substituir)"
                      : "Cole sua chave API OpenAI (sk-...)"
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs"
                />
              </div>

              <div className="pt-4 flex justify-between">
                <button
                  type="button"
                  onClick={() => goToStep(2)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-300 text-sm font-medium"
                >
                  <ArrowLeft className="h-4 w-4" /> Voltar
                </button>
                <button
                  type="button"
                  onClick={() => goToStep(4)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700"
                >
                  Avançar <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* ETAPA 4 */}
          {step === 4 && (
            <div className="space-y-6">
              <div>
                <h1 className="text-xl font-bold">Etapa 4 — Empresas Preferidas</h1>
                <p className="text-sm text-slate-600">
                  Adicione manualmente ou importe via CSV as empresas onde deseja trabalhar.
                </p>
              </div>

              <form onSubmit={handleAddCompany} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div className="relative">
                  <input
                    type="text"
                    required
                    value={newCompName}
                    onChange={(e) => handleCompanySearch(e.target.value, "")}
                    placeholder="Nome da empresa"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                  {companySuggestions.length > 0 && (
                    <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg z-20 max-h-56 overflow-y-auto">
                      {companySuggestions.map((sug) => (
                        <button
                          key={sug.id}
                          type="button"
                          onClick={() => selectCompanySuggestion(sug)}
                          className="w-full text-left px-3 py-2 text-xs hover:bg-indigo-50 border-b border-slate-100 last:border-0"
                        >
                          <div className="font-semibold text-slate-900">
                            {sug.name}
                            {sug.city || sug.state
                              ? ` — ${[sug.city, sug.state].filter(Boolean).join("/")}`
                              : ""}
                          </div>
                          <div className="text-[11px] text-slate-500 truncate">
                            {sug.sector || "Setor não informado"}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <input
                  type="url"
                  value={newCompCareers}
                  onChange={(e) => setNewCompCareers(e.target.value)}
                  placeholder="Página Trabalhe Conosco (opcional)"
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
                <select
                  value={newCompPriority}
                  onChange={(e) =>
                    setNewCompPriority(e.target.value as "alta" | "media" | "baixa")
                  }
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="alta">Prioridade Alta</option>
                  <option value="media">Prioridade Média</option>
                  <option value="baixa">Prioridade Baixa</option>
                </select>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-lg bg-indigo-600 text-white text-sm font-semibold px-4 py-2 hover:bg-indigo-700"
                >
                  Adicionar empresa
                </button>
              </form>

              {/* Opção alternativa: digitar segmento de interesse com sugestões de empresas */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="text-xs font-bold text-slate-800">
                  Ou adicione um segmento de preferência
                </div>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="text"
                    value={segmentInput}
                    onChange={async (e) => {
                      const val = e.target.value;
                      setSegmentInput(val);
                      if (val.trim().length >= 2) {
                        try {
                          setSegmentCompanies(await api.searchCompanyCatalog("", val.trim()));
                        } catch {
                          setSegmentCompanies([]);
                        }
                      } else {
                        setSegmentCompanies([]);
                      }
                    }}
                    placeholder="Digite o segmento (ex.: Cosméticos, Saúde, Indústria Química, Agronegócio...)"
                    className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs"
                  />
                  <button
                    type="button"
                    onClick={async () => {
                      const seg = segmentInput.trim();
                      if (!seg) return;
                      const current = prefs.preferred_sectors || [];
                      if (!current.includes(seg)) {
                        const updated = await api.updatePreferences({
                          preferred_sectors: [...current, seg],
                        });
                        setPrefs(updated);
                      }
                      setSegmentInput("");
                      setSegmentCompanies([]);
                    }}
                    className="px-4 py-2 rounded-lg bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 shrink-0"
                  >
                    Adicionar segmento
                  </button>
                </div>

                {segmentCompanies.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-[11px] font-semibold text-slate-600">
                      Empresas encontradas neste segmento (clique para adicionar às preferidas):
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {segmentCompanies.map((sc) => (
                        <button
                          key={sc.id}
                          type="button"
                          onClick={async () => {
                            try {
                              const created = await api.addFavoriteCompany({
                                name: sc.name,
                                careers_page_url: sc.careers_page_url || undefined,
                                city: sc.city || undefined,
                                state: sc.state || undefined,
                                sector: sc.sector || undefined,
                                priority: newCompPriority,
                              });
                              setCompanies((prev) => [created, ...prev]);
                            } catch {
                              // already added
                            }
                          }}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-white border border-indigo-200 text-[11px] font-medium text-indigo-800 hover:bg-indigo-50"
                        >
                          <Plus className="h-3 w-3" /> {sc.name}
                          {sc.city ? ` (${sc.city}/${sc.state})` : ""}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {(prefs.preferred_sectors || []).length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {(prefs.preferred_sectors || []).map((seg) => (
                      <span
                        key={seg}
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-600 text-white text-xs font-medium"
                      >
                        {seg}
                        <button
                          type="button"
                          onClick={async () => {
                            const updated = await api.updatePreferences({
                              preferred_sectors: (prefs.preferred_sectors || []).filter(
                                (x) => x !== seg
                              ),
                            });
                            setPrefs(updated);
                          }}
                          className="hover:text-indigo-200"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold cursor-pointer hover:bg-slate-50">
                  <FileUp className="h-4 w-4 text-indigo-600" />
                  Importar empresas por CSV (colunas: nome, site, carreiras, cidade, estado, setor, prioridade)
                  <input type="file" accept=".csv" onChange={handleCsvUpload} className="hidden" />
                </label>
              </div>

              <div className="space-y-2">
                {companies.map((c) => (
                  <div
                    key={c.id}
                    className="p-3 rounded-xl border border-slate-200 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-sm font-semibold">{c.company.name}</div>
                      <div className="text-xs text-slate-500">
                        {[c.company.city, c.company.state].filter(Boolean).join("/") || "Localidade não informada"}
                        {c.company.sector && ` · ${c.company.sector}`}
                        {` · Prioridade ${c.priority} · Status: ${c.monitoring_status}`}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-xs font-bold text-slate-800">
                    Conectar ChatGPT / OpenAI (Opcional — Altamente Recomendado)
                  </div>
                  <a
                    href="https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key"
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] font-semibold text-indigo-600 hover:underline"
                  >
                    Como criar chave na OpenAI
                  </a>
                </div>
                <p className="text-[11px] text-slate-600">
                  Permite adaptar seu currículo ATS em PDF e respostas de recrutamento usando o Agente Especialista Estratégico com seus fatos reais.
                </p>
                <input
                  type="password"
                  value={prefs.openai_api_key || ""}
                  onChange={(e) => setPrefs({ ...prefs, openai_api_key: e.target.value })}
                  placeholder={
                    prefs.has_openai_key
                      ? "Chave OpenAI já conectada (digite outra para substituir)"
                      : "Cole sua chave API OpenAI (sk-...)"
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs"
                />
              </div>

              <div className="pt-4 flex justify-between">
                <button
                  type="button"
                  onClick={() => goToStep(3)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-300 text-sm font-medium"
                >
                  <ArrowLeft className="h-4 w-4" /> Voltar
                </button>
                <button
                  type="button"
                  onClick={() => goToStep(5)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700"
                >
                  Avançar <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* ETAPA 5 */}
          {step === 5 && (
            <div className="space-y-5">
              <div>
                <h1 className="text-xl font-bold">Etapa 5 — Preferências Profissionais</h1>
                <p className="text-sm text-slate-600">
                  Não presumimos respostas não informadas. Preencha apenas o que desejar.
                </p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Cidade atual</label>
                  <input
                    type="text"
                    value={prefs.current_city || ""}
                    onChange={(e) => setPrefs({ ...prefs, current_city: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Estado atual</label>
                  <input
                    type="text"
                    value={prefs.current_state || ""}
                    onChange={(e) => setPrefs({ ...prefs, current_state: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">
                    Raio de busca da cidade atual (km)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={1000}
                    value={prefs.max_commute_km ?? ""}
                    onChange={(e) =>
                      setPrefs({
                        ...prefs,
                        max_commute_km: e.target.value ? Number(e.target.value) : null,
                      })
                    }
                    placeholder="Ex.: 50"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div className="flex items-end pb-2">
                  <label className="inline-flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={(prefs.desired_locations || []).includes("Brasil")}
                      onChange={(e) => {
                        const current = (prefs.desired_locations || []).filter(
                          (x) => x !== "Brasil"
                        );
                        setPrefs({
                          ...prefs,
                          desired_locations: e.target.checked
                            ? [...current, "Brasil"]
                            : current,
                          relocation_available: e.target.checked,
                        });
                      }}
                    />
                    Buscar vagas em todo o Brasil
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Modalidades de trabalho aceitas
                </label>
                <div className="flex flex-wrap gap-2">
                  {[
                    { key: "remoto", label: "Remoto" },
                    { key: "hibrido", label: "Híbrido" },
                    { key: "presencial", label: "Presencial" },
                  ].map((m) => {
                    const active = (prefs.work_modalities || []).includes(m.key);
                    return (
                      <button
                        key={m.key}
                        type="button"
                        onClick={() => {
                          const current = prefs.work_modalities || [];
                          setPrefs({
                            ...prefs,
                            work_modalities: active
                              ? current.filter((x) => x !== m.key)
                              : [...current, m.key],
                          });
                        }}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition ${
                          active
                            ? "bg-indigo-600 text-white border-indigo-600"
                            : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                        }`}
                      >
                        {active ? `✓ ${m.label}` : m.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">
                    Pretensão salarial mínima (R$)
                  </label>
                  <input
                    type="number"
                    value={prefs.min_salary_brl ?? ""}
                    onChange={(e) =>
                      setPrefs({
                        ...prefs,
                        min_salary_brl: e.target.value ? Number(e.target.value) : null,
                      })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">
                    Pretensão salarial desejada (R$)
                  </label>
                  <input
                    type="number"
                    value={prefs.desired_salary_brl ?? ""}
                    onChange={(e) =>
                      setPrefs({
                        ...prefs,
                        desired_salary_brl: e.target.value ? Number(e.target.value) : null,
                      })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <p className="text-xs text-slate-500">
                <strong>Observação:</strong> A pretensão salarial será usada apenas para preencher formulários de candidatura e nunca excluirá vagas com salário &ldquo;a combinar&rdquo; ou não divulgado.
              </p>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-xs font-bold text-slate-800">
                    Conectar ChatGPT / OpenAI (Opcional — Altamente Recomendado)
                  </div>
                  <a
                    href="https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key"
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] font-semibold text-indigo-600 hover:underline"
                  >
                    Como criar chave na OpenAI
                  </a>
                </div>
                <p className="text-[11px] text-slate-600">
                  Permite adaptar seu currículo ATS em PDF e respostas de recrutamento usando o Agente Especialista Estratégico com seus fatos reais.
                </p>
                <input
                  type="password"
                  value={prefs.openai_api_key || ""}
                  onChange={(e) => setPrefs({ ...prefs, openai_api_key: e.target.value })}
                  placeholder={
                    prefs.has_openai_key
                      ? "Chave OpenAI já conectada (digite outra para substituir)"
                      : "Cole sua chave API OpenAI (sk-...)"
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs"
                />
              </div>

              <div className="pt-4 flex justify-between">
                <button
                  type="button"
                  onClick={() => goToStep(4)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-300 text-sm font-medium"
                >
                  <ArrowLeft className="h-4 w-4" /> Voltar
                </button>
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => handleSavePreferences(6, false)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700"
                >
                  Salvar e avançar <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* ETAPA 6 */}
          {step === 6 && (
            <div className="space-y-5">
              <div>
                <h1 className="text-xl font-bold">Etapa 6 — Configuração dos Agentes</h1>
                <p className="text-sm text-slate-600">
                  Defina os limites operacionais. O modo de candidatura é sempre supervisionado.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200 flex items-start gap-3">
                <ShieldCheck className="h-5 w-5 text-indigo-600 shrink-0 mt-0.5" />
                <div className="text-xs text-indigo-900">
                  <strong>Modo Supervisionado Obrigatório:</strong> Nenhum agente enviará
                  candidaturas ou responderá recrutadores sem sua aprovação individual explícita.
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">
                    Frequência de buscas diárias
                  </label>
                  <select
                    value={prefs.search_frequency_hours ?? 24}
                    onChange={(e) =>
                      setPrefs({ ...prefs, search_frequency_hours: Number(e.target.value) })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value={24}>1x por dia</option>
                    <option value={12}>2x por dia</option>
                    <option value={8}>3x por dia</option>
                    <option value={6}>4x por dia</option>
                    <option value={48}>A cada 2 dias</option>
                    <option value={168}>1x por semana</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">
                    Máx. oportunidades recomendadas
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={prefs.max_recommended_jobs ?? 20}
                    onChange={(e) =>
                      setPrefs({ ...prefs, max_recommended_jobs: Number(e.target.value) })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">
                    Pontuação mínima de aderência
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={prefs.min_match_score ?? 65}
                    onChange={(e) =>
                      setPrefs({ ...prefs, min_match_score: Number(e.target.value) })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-xs font-bold text-slate-800">
                    Conectar ChatGPT / OpenAI (Opcional — Altamente Recomendado)
                  </div>
                  <a
                    href="https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key"
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] font-semibold text-indigo-600 hover:underline"
                  >
                    Como criar chave na OpenAI
                  </a>
                </div>
                <p className="text-[11px] text-slate-600">
                  Permite adaptar seu currículo ATS em PDF e respostas de recrutamento usando o Agente Especialista Estratégico com seus fatos reais.
                </p>
                <input
                  type="password"
                  value={prefs.openai_api_key || ""}
                  onChange={(e) => setPrefs({ ...prefs, openai_api_key: e.target.value })}
                  placeholder={
                    prefs.has_openai_key
                      ? "Chave OpenAI já conectada (digite outra para substituir)"
                      : "Cole sua chave API OpenAI (sk-...)"
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs"
                />
              </div>

              <div className="pt-4 flex justify-between">
                <button
                  type="button"
                  onClick={() => goToStep(5)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-300 text-sm font-medium"
                >
                  <ArrowLeft className="h-4 w-4" /> Voltar
                </button>
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => handleSavePreferences(6, true)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700"
                >
                  <CheckCircle2 className="h-4 w-4" /> Concluir Onboarding
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

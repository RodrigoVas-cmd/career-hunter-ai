"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink, Plus, Radar, Search, Sparkles, Star, Trash2 } from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, ApiError, JobPosting } from "@/lib/api";

export default function RadarPage() {
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [q, setQ] = useState("");
  const [modality, setModality] = useState("");
  const [onlyFavs, setOnlyFavs] = useState(false);
  const [respectPrefs, setRespectPrefs] = useState(true);

  // Connector form
  const [sourceKind, setSourceKind] = useState<"greenhouse" | "lever" | "jsonld">("greenhouse");
  const [target, setTarget] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Manual job form
  const [showManual, setShowManual] = useState(false);
  const [mCompany, setMCompany] = useState("");
  const [mTitle, setMTitle] = useState("");
  const [mUrl, setMUrl] = useState("");
  const [mDesc, setMDesc] = useState("");
  const [mModality, setMModality] = useState("remoto");
  const [compSuggestions, setCompSuggestions] = useState<Array<{ id: string; name: string; city: string | null; state: string | null }>>([]);
  const [knownRoles, setKnownRoles] = useState<string[]>([]);
  const [showRoleSuggestions, setShowRoleSuggestions] = useState(false);

  function fetchJobs() {
    api
      .listJobs({
        q: q || undefined,
        modality: modality || undefined,
        only_favorites: onlyFavs,
        respect_preferences: respectPrefs,
      })
      .then(setJobs)
      .catch(() => {});
  }

  useEffect(() => {
    fetchJobs();
  }, [onlyFavs, modality, respectPrefs]);

  useEffect(() => {
    Promise.all([api.listTargetRoles(), api.listExperiences(), api.getPreferences()])
      .then(([roles, exps, pref]) => {
        const active = roles.filter((r) => r.status === "ativo").map((r) => r.title);
        const titles = Array.from(
          new Set([
            ...roles.map((r) => r.title),
            ...exps.map((e) => e.role_title),
          ])
        ).filter(Boolean);
        setActiveRoles(active.length > 0 ? active : titles);
        setKnownRoles(titles);
        setPrimaryRole(active[0] || titles[0] || "");
        setUserLocation([pref.current_city, pref.current_state].filter(Boolean).join(" "));
      })
      .catch(() => {});
  }, []);

  const [activeRoles, setActiveRoles] = useState<string[]>([]);
  const [primaryRole, setPrimaryRole] = useState("");
  const [userLocation, setUserLocation] = useState("");

  async function handleAutoDiscover() {
    setLoading(true);
    setErr(null);
    setMsg(null);
    try {
      const res = await api.discoverAuto();
      if (!res.allows_remote && res.created_count === 0 && res.sources_checked.length === 0) {
        setMsg(
          "Busca concluída respeitando seus filtros (Híbrido/Presencial e localidade). Nenhuma empresa favorita com conector público tinha vagas abertas compatíveis no momento; use os atalhos abaixo para buscar no LinkedIn, Indeed, Gupy, Catho ou Vagas.com.br."
        );
      } else {
        setMsg(
          `Busca automática concluída! ${res.created_count} nova(s) vaga(s) compatível(is), ${res.updated_count} atualizada(s) e ${res.matched_count} analisada(s) no Motor de Aderência.`
        );
      }
      fetchJobs();
    } catch (e2) {
      setErr(e2 instanceof ApiError ? e2.message : "Erro na busca automática.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDiscover(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErr(null);
    setMsg(null);
    try {
      const res = await api.discoverViaConnector({
        source_kind: sourceKind,
        target: target.trim(),
        company_name: companyName.trim() || undefined,
      });
      setMsg(
        `Conector ${res.source_kind}: ${res.fetched_count} vaga(s) encontrada(s), ${res.created_count} nova(s), ${res.updated_count} atualizada(s).`
      );
      setTarget("");
      fetchJobs();
    } catch (e2) {
      setErr(e2 instanceof ApiError ? e2.message : "Erro ao consultar conector.");
    } finally {
      setLoading(false);
    }
  }

  async function handleManualCreate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErr(null);
    setMsg(null);
    try {
      await api.createManualJob({
        company_name: mCompany.trim(),
        title: mTitle.trim(),
        original_url: mUrl.trim(),
        description: mDesc.trim(),
        modality: mModality,
      });
      setMsg("Vaga registrada e normalizada com sucesso.");
      setMCompany("");
      setMTitle("");
      setMUrl("");
      setMDesc("");
      setShowManual(false);
      fetchJobs();
    } catch (e2) {
      setErr(e2 instanceof ApiError ? e2.message : "Erro ao cadastrar vaga.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">Radar de Vagas</h1>
            <p className="text-sm text-slate-600">
              Conectores autorizados (Greenhouse, Lever, JSON-LD) e registro manual com deduplicação.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowManual((v) => !v)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white border border-slate-300 text-xs font-semibold hover:bg-slate-50"
          >
            <Plus className="h-4 w-4 text-indigo-600" />
            Registrar vaga manual (LinkedIn/Gupy/Indeed)
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

        {/* One-Click Auto Search for Non-Technical Users */}
        <div className="bg-white p-5 rounded-2xl border border-indigo-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Radar className="h-5 w-5 text-indigo-600" />
                Busca Automática Inteligente
              </div>
              <p className="text-xs text-slate-600 mt-0.5">
                Com 1 clique, buscamos vagas nas fontes autorizadas para seus cargos-alvo e já calculamos sua aderência (0–100).
              </p>
            </div>
            <button
              type="button"
              onClick={handleAutoDiscover}
              disabled={loading}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 shrink-0"
            >
              {loading ? "Buscando vagas..." : "Buscar Vagas Automaticamente"}
            </button>
          </div>

          {primaryRole && (
            <div className="pt-3 border-t border-slate-100 space-y-2">
              <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-700">
                <span>Atalhos já filtrados para abrir portais externos:</span>
                {activeRoles.length > 1 ? (
                  <select
                    value={primaryRole}
                    onChange={(e) => setPrimaryRole(e.target.value)}
                    className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-800"
                  >
                    {activeRoles.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span>{primaryRole}</span>
                )}
                {userLocation && <span className="text-slate-500">· {userLocation}</span>}
              </div>
              <div className="flex flex-wrap gap-2 text-xs">
                <a
                  href={`https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(primaryRole)}&location=${encodeURIComponent(userLocation || "Brasil")}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 hover:bg-slate-100 font-medium"
                >
                  LinkedIn Jobs <ExternalLink className="h-3 w-3" />
                </a>
                <a
                  href={`https://br.indeed.com/jobs?q=${encodeURIComponent(primaryRole)}&l=${encodeURIComponent(userLocation || "Brasil")}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 hover:bg-slate-100 font-medium"
                >
                  Indeed <ExternalLink className="h-3 w-3" />
                </a>
                <a
                  href={`https://portal.gupy.io/job-search/term=${encodeURIComponent(primaryRole)}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 hover:bg-slate-100 font-medium"
                >
                  Gupy <ExternalLink className="h-3 w-3" />
                </a>
                <a
                  href={`https://www.catho.com.br/vagas/${encodeURIComponent(primaryRole.toLowerCase().replace(/\s+/g, "-"))}/`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 hover:bg-slate-100 font-medium"
                >
                  Catho <ExternalLink className="h-3 w-3" />
                </a>
                <a
                  href={`https://www.vagas.com.br/vagas-de-${encodeURIComponent(primaryRole.toLowerCase().replace(/\s+/g, "-"))}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 hover:bg-slate-100 font-medium"
                >
                  Vagas.com.br <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Advanced Connector Box (collapsed by default for non-technical users) */}
        <details className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
          <summary className="text-xs font-bold text-slate-600 cursor-pointer">
            Opções avançadas: buscar manualmente em Greenhouse, Lever ou JSON-LD
          </summary>
          <form onSubmit={handleDiscover} className="mt-3 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <select
                value={sourceKind}
                onChange={(e) =>
                  setSourceKind(e.target.value as "greenhouse" | "lever" | "jsonld")
                }
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="greenhouse">Greenhouse (board token)</option>
                <option value="lever">Lever (company slug)</option>
                <option value="jsonld">Página JSON-LD (URL)</option>
              </select>
              <input
                type="text"
                required
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder={
                  sourceKind === "jsonld"
                    ? "https://carreiras.empresa.com"
                    : "Ex.: nubank, stripe, airbnb"
                }
                className="sm:col-span-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <button
                type="submit"
                disabled={loading}
                className="rounded-lg bg-indigo-600 text-white text-sm font-semibold px-4 py-2 hover:bg-indigo-700 disabled:opacity-50"
              >
                {loading ? "Buscando..." : "Executar conector"}
              </button>
            </div>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Nome da empresa (opcional)"
              className="w-full sm:w-1/2 rounded-lg border border-slate-300 px-3 py-1.5 text-xs"
            />
          </form>
        </details>

        {/* Manual Job Form */}
        {showManual && (
          <form
            onSubmit={handleManualCreate}
            className="bg-white p-5 rounded-2xl border border-indigo-200 shadow-sm space-y-3"
          >
            <h2 className="text-sm font-bold">Registrar Vaga Manualmente</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="relative">
                <input
                  type="text"
                  required
                  value={mCompany}
                  onChange={async (e) => {
                    const val = e.target.value;
                    setMCompany(val);
                    if (val.trim().length >= 2) {
                      try {
                        setCompSuggestions(await api.searchCompanyCatalog(val.trim()));
                      } catch {
                        setCompSuggestions([]);
                      }
                    } else {
                      setCompSuggestions([]);
                    }
                  }}
                  placeholder="Empresa (digite para buscar)"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
                {compSuggestions.length > 0 && (
                  <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg z-20 max-h-48 overflow-y-auto">
                    {compSuggestions.map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => {
                          setMCompany(s.name);
                          setCompSuggestions([]);
                        }}
                        className="w-full text-left px-3 py-2 text-xs hover:bg-indigo-50 border-b border-slate-100 last:border-0"
                      >
                        <span className="font-semibold">{s.name}</span>
                        {(s.city || s.state) && (
                          <span className="text-slate-500">
                            {" "}
                            — {[s.city, s.state].filter(Boolean).join("/")}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="relative">
                <input
                  type="text"
                  required
                  value={mTitle}
                  onFocus={() => setShowRoleSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowRoleSuggestions(false), 150)}
                  onChange={(e) => {
                    setMTitle(e.target.value);
                    setShowRoleSuggestions(true);
                  }}
                  placeholder="Cargo (digite ou escolha)"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
                {showRoleSuggestions &&
                  knownRoles.filter((r) =>
                    !mTitle.trim() || r.toLowerCase().includes(mTitle.toLowerCase())
                  ).length > 0 && (
                    <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg z-20 max-h-48 overflow-y-auto">
                      {knownRoles
                        .filter(
                          (r) =>
                            !mTitle.trim() ||
                            r.toLowerCase().includes(mTitle.toLowerCase())
                        )
                        .map((r) => (
                          <button
                            key={r}
                            type="button"
                            onMouseDown={() => {
                              setMTitle(r);
                              setShowRoleSuggestions(false);
                            }}
                            className="w-full text-left px-3 py-2 text-xs hover:bg-indigo-50 border-b border-slate-100 last:border-0 font-medium"
                          >
                            {r}
                          </button>
                        ))}
                    </div>
                  )}
              </div>

              <select
                value={mModality}
                onChange={(e) => setMModality(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="remoto">Remoto</option>
                <option value="hibrido">Híbrido</option>
                <option value="presencial">Presencial</option>
              </select>
            </div>
            <input
              type="url"
              required
              value={mUrl}
              onChange={(e) => setMUrl(e.target.value)}
              placeholder="Link original da vaga"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <textarea
              required
              rows={3}
              value={mDesc}
              onChange={(e) => setMDesc(e.target.value)}
              placeholder="Cole aqui a descrição e requisitos da vaga..."
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-semibold"
            >
              Salvar vaga
            </button>
          </form>
        )}

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[200px] flex gap-2">
            <input
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Filtrar por cargo ou empresa..."
              className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            />
            <button
              type="button"
              onClick={fetchJobs}
              className="px-3 py-2 rounded-lg bg-slate-900 text-white text-sm"
            >
              <Search className="h-4 w-4" />
            </button>
          </div>
          <select
            value={modality}
            onChange={(e) => setModality(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
          >
            <option value="">Todas modalidades</option>
            <option value="remoto">Remoto</option>
            <option value="hibrido">Híbrido</option>
            <option value="presencial">Presencial</option>
          </select>
          <label className="inline-flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={onlyFavs}
              onChange={(e) => setOnlyFavs(e.target.checked)}
            />
            Apenas empresas favoritas
          </label>
          <label className="inline-flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={respectPrefs}
              onChange={(e) => setRespectPrefs(e.target.checked)}
            />
            Filtrar por meu perfil (cargos e localidade)
          </label>
        </div>

        {/* Jobs List */}
        <div className="space-y-3">
          {jobs.length === 0 ? (
            <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-sm text-slate-500">
              Nenhuma vaga descoberta ainda. Execute um conector acima ou registre uma vaga manual.
            </div>
          ) : (
            jobs.map((j) => (
              <div
                key={j.id}
                className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div>
                  <div className="flex items-center gap-2 font-semibold text-sm">
                    {j.title}
                    {j.is_favorite_company && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 text-[11px] font-semibold border border-amber-200">
                        <Star className="h-3 w-3 fill-amber-500 text-amber-500" />
                        Empresa Favorita
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    {j.company_name}
                    {j.location && ` · ${j.location}`}
                    {j.modality && ` · ${j.modality}`}
                    {j.seniority && ` · ${j.seniority}`}
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2 shrink-0">
                  <Link
                    href="/app/recomendadas"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 text-xs font-semibold text-indigo-700 hover:bg-indigo-100"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    Vagas Recomendadas
                  </Link>
                  <a
                    href={j.original_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    Ver original <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        await api.deleteJob(j.id);
                        setJobs((prev) => prev.filter((item) => item.id !== j.id));
                      } catch (e2) {
                        setErr(e2 instanceof ApiError ? e2.message : "Erro ao excluir vaga.");
                      }
                    }}
                    title="Excluir vaga"
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-red-200 text-xs font-semibold text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Excluir
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </AppShell>
  );
}

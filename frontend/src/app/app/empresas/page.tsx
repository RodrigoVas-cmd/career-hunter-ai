"use client";

import { useEffect, useState } from "react";
import { ExternalLink, FileUp, Plus, Radar, Trash2 } from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, ApiError, CompanyWatchResult, FavoriteCompany } from "@/lib/api";

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<FavoriteCompany[]>([]);
  const [name, setName] = useState("");
  const [careersUrl, setCareersUrl] = useState("");
  const [sector, setSector] = useState("");
  const [city, setCity] = useState("");
  const [stateUf, setStateUf] = useState("");
  const [priority, setPriority] = useState<"alta" | "media" | "baixa">("alta");
  const [suggestions, setSuggestions] = useState<
    Array<{
      id: string;
      name: string;
      careers_page_url: string | null;
      city: string | null;
      state: string | null;
      sector: string | null;
    }>
  >([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [watching, setWatching] = useState(false);
  const [watchResult, setWatchResult] = useState<CompanyWatchResult | null>(null);

  useEffect(() => {
    api.listFavoriteCompanies().then(setCompanies);
  }, []);

  async function handleCompanySearch(val: string, sec: string) {
    setName(val);
    setSector(sec);
    if (val.trim().length >= 2 || sec.trim().length > 0) {
      try {
        setSuggestions(await api.searchCompanyCatalog(val.trim(), sec.trim()));
      } catch {
        setSuggestions([]);
      }
    } else {
      setSuggestions([]);
    }
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    try {
      const created = await api.addFavoriteCompany({
        name: name.trim(),
        careers_page_url: careersUrl.trim() || undefined,
        sector: sector.trim() || undefined,
        city: city.trim() || undefined,
        state: stateUf.trim() || undefined,
        priority,
      });
      setCompanies((prev) => [created, ...prev]);
      setName("");
      setCareersUrl("");
      setSector("");
      setCity("");
      setStateUf("");
      setSuggestions([]);
      setMsg("Empresa adicionada à sua lista.");
    } catch (e2) {
      setErr(e2 instanceof ApiError ? e2.message : "Erro ao adicionar empresa.");
    }
  }

  async function handleCsv(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setErr(null);
    setMsg(null);
    try {
      const res = await api.importCompaniesCsv(file);
      const list = await api.listFavoriteCompanies();
      setCompanies(list);
      setMsg(`${res.imported_count} importada(s), ${res.skipped_count} ignorada(s).`);
    } catch (e2) {
      setErr(e2 instanceof ApiError ? e2.message : "Erro ao importar CSV.");
    }
  }

  async function handleDelete(id: string) {
    await api.deleteFavoriteCompany(id);
    setCompanies((prev) => prev.filter((c) => c.id !== id));
  }

  async function handleCompanyWatch() {
    setWatching(true);
    setErr(null);
    setMsg(null);
    try {
      const res = await api.runCompanyWatch();
      setWatchResult(res);
      const list = await api.listFavoriteCompanies();
      setCompanies(list);
      setMsg(
        `Company Watch concluído: ${res.monitored_count} monitorada(s), ${res.total_jobs_found} vaga(s) encontrada(s), ${res.error_count} erro(s).`
      );
    } catch (e2) {
      setErr(e2 instanceof ApiError ? e2.message : "Erro ao executar Company Watch.");
    } finally {
      setWatching(false);
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">Minhas Empresas</h1>
            <p className="text-sm text-slate-600">
              Cadastre empresas desejadas e execute o Company Watch nas páginas de carreiras.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={handleCompanyWatch}
              disabled={watching}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 disabled:opacity-50"
            >
              <Radar className="h-4 w-4" />
              {watching ? "Monitorando..." : "Executar Company Watch"}
            </button>
            <label className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-slate-300 text-xs font-semibold cursor-pointer hover:bg-slate-50">
              <FileUp className="h-4 w-4 text-indigo-600" />
              Importar CSV
              <input type="file" accept=".csv" onChange={handleCsv} className="hidden" />
            </label>
          </div>
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

        {watchResult && (
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div className="text-xs font-bold text-slate-700">Último resultado do Company Watch</div>
            {watchResult.results.map((r) => (
              <div key={r.favorite_company_id} className="text-xs flex items-center justify-between gap-2 border-t border-slate-100 pt-2">
                <div>
                  <span className="font-semibold">{r.company_name}</span> — {r.status} ({r.jobs_found} vaga(s))
                  {r.error_message && <p className="text-amber-700">{r.error_message}</p>}
                </div>
                {r.careers_page_url && (
                  <a href={r.careers_page_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline shrink-0">
                    Abrir fonte
                  </a>
                )}
              </div>
            ))}
          </div>
        )}

        <form
          onSubmit={handleAdd}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-5 gap-3"
        >
          <div className="relative space-y-2">
            <input
              type="text"
              required
              value={name}
              onChange={(e) => handleCompanySearch(e.target.value, sector)}
              placeholder="Nome da empresa (digite para buscar)"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <select
              value={sector}
              onChange={(e) => handleCompanySearch(name, e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-700"
            >
              <option value="">Filtrar por segmento (opcional)</option>
              <option value="Indústria Química">Indústria Química / Construção Civil</option>
              <option value="Materiais de Construção">Materiais de Construção</option>
              <option value="Equipamentos Elétricos">Equipamentos Elétricos / Indústria</option>
              <option value="Siderurgia">Siderurgia</option>
              <option value="Bens de Consumo">Bebidas / Cosméticos / Bens de Consumo</option>
              <option value="Aeroespacial">Aeroespacial</option>
              <option value="Papel e Celulose">Papel e Celulose</option>
              <option value="Tecnologia">Tecnologia / E-commerce</option>
              <option value="Financeiro">Financeiro</option>
            </select>
            {suggestions.length > 0 && (
              <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg z-20 max-h-56 overflow-y-auto">
                {suggestions.map((sug) => (
                  <button
                    key={sug.id}
                    type="button"
                    onClick={() => {
                      setName(sug.name);
                      setCareersUrl(sug.careers_page_url || "");
                      setSector(sug.sector || "");
                      setCity(sug.city || "");
                      setStateUf(sug.state || "");
                      setSuggestions([]);
                    }}
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
            value={careersUrl}
            onChange={(e) => setCareersUrl(e.target.value)}
            placeholder="Página de carreiras"
            className="sm:col-span-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <input
            type="text"
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            placeholder="Setor (ex.: Tecnologia)"
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <div className="flex gap-2">
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as "alta" | "media" | "baixa")}
              className="rounded-lg border border-slate-300 px-2 py-2 text-sm"
            >
              <option value="alta">Alta</option>
              <option value="media">Média</option>
              <option value="baixa">Baixa</option>
            </select>
            <button
              type="submit"
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 text-white px-3 py-2 text-sm font-semibold"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        </form>

        <div className="space-y-3">
          {companies.length === 0 ? (
            <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-sm text-slate-500">
              Nenhuma empresa preferida cadastrada ainda.
            </div>
          ) : (
            companies.map((c) => (
              <div
                key={c.id}
                className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between gap-4"
              >
                <div>
                  <div className="font-semibold text-sm flex items-center gap-2">
                    {c.company.name}
                    {c.company.careers_page_url && (
                      <a
                        href={c.company.careers_page_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-600 hover:text-indigo-800"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    )}
                  </div>
                  <div className="text-xs text-slate-500">
                    {c.company.sector || "Setor não informado"} · Prioridade {c.priority} · Status:{" "}
                    {c.monitoring_status}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleDelete(c.id)}
                  className="p-2 text-slate-400 hover:text-red-600"
                  aria-label="Remover empresa"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </AppShell>
  );
}

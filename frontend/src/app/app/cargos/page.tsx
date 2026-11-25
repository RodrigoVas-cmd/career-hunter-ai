"use client";

import { useEffect, useState } from "react";
import { Pause, Play, Plus, Trash2 } from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, TargetRole, TargetRoleSuggestion } from "@/lib/api";

export default function TargetRolesPage() {
  const [roles, setRoles] = useState<TargetRole[]>([]);
  const [suggestions, setSuggestions] = useState<TargetRoleSuggestion[]>([]);
  const [title, setTitle] = useState("");
  const [seniority, setSeniority] = useState("Sênior");
  const [priority, setPriority] = useState<"alta" | "media" | "baixa">("alta");
  const [minSalary, setMinSalary] = useState("");
  const [maxSalary, setMaxSalary] = useState("");
  const [editingSalaryId, setEditingSalaryId] = useState<string | null>(null);
  const [editMinSalary, setEditMinSalary] = useState("");
  const [editMaxSalary, setEditMaxSalary] = useState("");

  useEffect(() => {
    api.listTargetRoles().then(setRoles);
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    const created = await api.createTargetRole({
      title: title.trim(),
      desired_seniority: seniority,
      priority,
      min_salary_brl: minSalary ? Number(minSalary) : null,
      desired_salary_brl: maxSalary ? Number(maxSalary) : null,
      status: "ativo",
    });
    setRoles((prev) => [created, ...prev]);
    setTitle("");
    setMinSalary("");
    setMaxSalary("");
  }

  async function handleSaveSalary(role: TargetRole) {
    const updated = await api.updateTargetRole(role.id, {
      min_salary_brl: editMinSalary ? Number(editMinSalary) : null,
      desired_salary_brl: editMaxSalary ? Number(editMaxSalary) : null,
    });
    setRoles((prev) => prev.map((r) => (r.id === role.id ? updated : r)));
    setEditingSalaryId(null);
  }

  async function toggleStatus(role: TargetRole) {
    const nextStatus = role.status === "ativo" ? "pausado" : "ativo";
    const updated = await api.updateTargetRole(role.id, { status: nextStatus });
    setRoles((prev) => prev.map((r) => (r.id === role.id ? updated : r)));
  }

  async function removeRole(id: string) {
    await api.deleteTargetRole(id);
    setRoles((prev) => prev.filter((r) => r.id !== id));
  }

  async function fetchSuggestions() {
    const data = await api.getRoleSuggestions();
    setSuggestions(data);
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Meus Cargos-Alvo</h1>
          <p className="text-sm text-slate-600">
            Configure os cargos desejados. Nenhuma sugestão da IA é ativada sem sua aprovação.
          </p>
        </div>

        <form
          onSubmit={handleCreate}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3"
        >
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Título do cargo-alvo"
              className="sm:col-span-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <select
              value={seniority}
              onChange={(e) => setSeniority(e.target.value)}
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
                className="flex-1 inline-flex items-center justify-center gap-1 rounded-lg bg-indigo-600 text-white text-sm font-semibold px-3 py-2"
              >
                <Plus className="h-4 w-4" /> Criar
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input
              type="number"
              min={0}
              value={minSalary}
              onChange={(e) => setMinSalary(e.target.value)}
              placeholder="Pretensão mínima para este cargo (R$ — opcional)"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              type="number"
              min={0}
              value={maxSalary}
              onChange={(e) => setMaxSalary(e.target.value)}
              placeholder="Pretensão máxima para este cargo (R$ — opcional)"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        </form>

        <div>
          <button
            type="button"
            onClick={fetchSuggestions}
            className="text-sm font-semibold text-indigo-600 hover:underline"
          >
            Sugerir cargos correlatos baseados no meu currículo
          </button>
          {suggestions.length > 0 && (
            <div className="mt-3 space-y-2">
              {suggestions.map((s, i) => (
                <div
                  key={i}
                  className="p-4 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-between gap-3"
                >
                  <div>
                    <div className="font-semibold text-sm">{s.title}</div>
                    <div className="text-xs text-slate-600">{s.justification}</div>
                  </div>
                  <button
                    type="button"
                    onClick={async () => {
                      const created = await api.createTargetRole({
                        title: s.title,
                        priority: "media",
                        status: "ativo",
                      });
                      setRoles((prev) => [created, ...prev]);
                      setSuggestions((prev) => prev.filter((_, idx) => idx !== i));
                    }}
                    className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold shrink-0"
                  >
                    Aprovar cargo
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-3">
          {roles.length === 0 ? (
            <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-sm text-slate-500">
              Nenhum cargo-alvo cadastrado ainda.
            </div>
          ) : (
            roles.map((r) => (
              <div
                key={r.id}
                className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-sm">{r.title}</div>
                  <div className="text-xs text-slate-500">
                    {r.desired_seniority || "Qualquer senioridade"} · Prioridade {r.priority} ·{" "}
                    <span
                      className={
                        r.status === "ativo"
                          ? "text-emerald-700 font-semibold"
                          : "text-slate-500"
                      }
                    >
                      {r.status}
                    </span>
                    {(r.min_salary_brl || r.desired_salary_brl) && (
                      <span className="ml-2 text-indigo-700 font-medium">
                        · Pretensão:{" "}
                        {r.min_salary_brl ? `R$ ${r.min_salary_brl.toLocaleString("pt-BR")}` : "—"}
                        {" a "}
                        {r.desired_salary_brl ? `R$ ${r.desired_salary_brl.toLocaleString("pt-BR")}` : "—"}
                      </span>
                    )}
                  </div>
                  {editingSalaryId === r.id ? (
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <input
                        type="number"
                        min={0}
                        value={editMinSalary}
                        onChange={(e) => setEditMinSalary(e.target.value)}
                        placeholder="Mín. R$"
                        className="w-28 rounded-lg border border-slate-300 px-2 py-1 text-xs"
                      />
                      <input
                        type="number"
                        min={0}
                        value={editMaxSalary}
                        onChange={(e) => setEditMaxSalary(e.target.value)}
                        placeholder="Máx. R$"
                        className="w-28 rounded-lg border border-slate-300 px-2 py-1 text-xs"
                      />
                      <button
                        type="button"
                        onClick={() => handleSaveSalary(r)}
                        className="px-2.5 py-1 rounded-lg bg-indigo-600 text-white text-xs font-semibold"
                      >
                        Salvar
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingSalaryId(null)}
                        className="px-2 py-1 rounded-lg border border-slate-200 text-xs text-slate-600"
                      >
                        Cancelar
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setEditingSalaryId(r.id);
                        setEditMinSalary(r.min_salary_brl ? String(r.min_salary_brl) : "");
                        setEditMaxSalary(r.desired_salary_brl ? String(r.desired_salary_brl) : "");
                      }}
                      className="mt-1 text-[11px] font-semibold text-indigo-600 hover:underline"
                    >
                      {r.min_salary_brl || r.desired_salary_brl
                        ? "Editar faixa salarial deste cargo"
                        : "+ Definir faixa salarial para este cargo"}
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => toggleStatus(r)}
                    className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
                    title={r.status === "ativo" ? "Pausar" : "Ativar"}
                  >
                    {r.status === "ativo" ? (
                      <Pause className="h-4 w-4" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => removeRole(r.id)}
                    className="p-2 rounded-lg text-slate-400 hover:text-red-600"
                    title="Excluir"
                  >
                    <Trash2 className="h-4 w-4" />
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

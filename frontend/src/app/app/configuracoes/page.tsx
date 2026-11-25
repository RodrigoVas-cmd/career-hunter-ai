"use client";

import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, ApiError, CareerPreference } from "@/lib/api";

export default function SettingsPage() {
  const [prefs, setPrefs] = useState<Partial<CareerPreference>>({});
  const [openaiKeyInput, setOpenaiKeyInput] = useState("");
  const [saved, setSaved] = useState(false);
  const [currPass, setCurrPass] = useState("");
  const [newPass, setNewPass] = useState("");
  const [passMsg, setPassMsg] = useState<string | null>(null);
  const [passErr, setPassErr] = useState<string | null>(null);

  useEffect(() => {
    api.getPreferences().then(setPrefs);
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    const payload: Partial<CareerPreference> = { ...prefs };
    if (openaiKeyInput.trim()) {
      payload.openai_api_key = openaiKeyInput.trim();
    }
    const updated = await api.updatePreferences(payload);
    setPrefs(updated);
    setOpenaiKeyInput("");
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Configurações & Preferências</h1>
          <p className="text-sm text-slate-600">
            Ajuste suas preferências profissionais e parâmetros dos agentes.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-indigo-50 border border-indigo-200 flex items-start gap-3">
          <ShieldCheck className="h-5 w-5 text-indigo-600 shrink-0 mt-0.5" />
          <div className="text-xs text-indigo-900">
            <strong>Modo de candidatura: {prefs.application_mode || "supervised"}</strong> — A
            execução é sempre supervisionada e exige sua aprovação explícita antes de qualquer envio.
          </div>
        </div>

        {saved && (
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-sm text-emerald-700">
            Preferências salvas com sucesso.
          </div>
        )}

        <form
          onSubmit={handleSave}
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4"
        >
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
                Raio da cidade atual (km)
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
                    const current = (prefs.desired_locations || []).filter((x) => x !== "Brasil");
                    setPrefs({
                      ...prefs,
                      desired_locations: e.target.checked ? [...current, "Brasil"] : current,
                      relocation_available: e.target.checked,
                    });
                  }}
                />
                Buscar vagas em todo o Brasil
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Salário mínimo (R$)
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
                Salário desejado (R$)
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
            <div className="sm:col-span-2">
              <p className="text-xs text-slate-500">
                <strong>Observação:</strong> A pretensão salarial será usada apenas para preencher formulários de candidatura e nunca excluirá vagas com salário &ldquo;a combinar&rdquo; ou não divulgado.
              </p>
            </div>
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
                Pontuação mínima de aderência (0–100)
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

          <div className="border-t border-slate-200 pt-4 space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-bold text-slate-800">
                Integração ChatGPT / OpenAI (Opcional)
              </label>
              <span
                className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                  prefs.has_openai_key
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-slate-100 text-slate-600"
                }`}
              >
                {prefs.has_openai_key ? "Chave configurada" : "Não configurada"}
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Conecte sua chave da OpenAI (<code>sk-...</code>) para adaptar o resumo do currículo ATS
              especificamente para cada vaga, mantendo 100% de fidelidade aos seus fatos verificados.
            </p>
            <div className="flex gap-2">
              <input
                type="password"
                value={openaiKeyInput}
                onChange={(e) => setOpenaiKeyInput(e.target.value)}
                placeholder={
                  prefs.has_openai_key
                    ? "Digite uma nova chave para substituir..."
                    : "Cole sua chave OpenAI (sk-...)"
                }
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              {prefs.has_openai_key && (
                <button
                  type="button"
                  onClick={async () => {
                    const updated = await api.updatePreferences({ openai_api_key: "" });
                    setPrefs(updated);
                  }}
                  className="px-3 py-2 rounded-lg border border-red-200 text-red-700 text-xs font-semibold hover:bg-red-50"
                >
                  Remover chave
                </button>
              )}
            </div>
          </div>

          <button
            type="submit"
            className="px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700"
          >
            Salvar configurações
          </button>
        </form>

        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setPassMsg(null);
            setPassErr(null);
            try {
              const res = await api.changePassword(currPass, newPass);
              setPassMsg(res.message);
              setCurrPass("");
              setNewPass("");
            } catch (err) {
              setPassErr(err instanceof ApiError ? err.message : "Erro ao alterar senha.");
            }
          }}
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4"
        >
          <h2 className="text-base font-bold text-slate-900">Segurança — Alterar senha</h2>
          {passErr && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">
              {passErr}
            </div>
          )}
          {passMsg && (
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-sm text-emerald-700">
              {passMsg}
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Senha atual</label>
              <input
                type="password"
                required
                value={currPass}
                onChange={(e) => setCurrPass(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Nova senha (mín. 8 caracteres)
              </label>
              <input
                type="password"
                required
                minLength={8}
                value={newPass}
                onChange={(e) => setNewPass(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          </div>
          <button
            type="submit"
            className="px-5 py-2.5 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800"
          >
            Atualizar senha
          </button>
        </form>
      </div>
    </AppShell>
  );
}

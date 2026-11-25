"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, CheckCircle2, ExternalLink, Play, Send, Star } from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, JobMatch } from "@/lib/api";

const CLASSIFICATION_LABEL: Record<string, { text: string; cls: string }> = {
  excelente_aderencia: { text: "Excelente aderência", cls: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  alta_aderencia: { text: "Alta aderência", cls: "bg-indigo-50 text-indigo-700 border-indigo-200" },
  aderencia_moderada: { text: "Aderência moderada", cls: "bg-amber-50 text-amber-700 border-amber-200" },
  baixa_prioridade: { text: "Baixa prioridade", cls: "bg-slate-100 text-slate-700 border-slate-200" },
  inelegivel: { text: "Inelegível", cls: "bg-red-50 text-red-700 border-red-200" },
};

export default function RecommendedJobsPage() {
  const router = useRouter();
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [onlyFavs, setOnlyFavs] = useState(false);
  const [running, setRunning] = useState(false);

  async function handlePrepareApplication(jobPostingId: string) {
    try {
      const app = await api.createApplication({ job_posting_id: jobPostingId });
      router.push(`/app/candidaturas?id=${app.id}`);
    } catch {
      router.push("/app/candidaturas");
    }
  }

  function loadMatches() {
    api
      .listJobMatches({ only_favorites: onlyFavs })
      .then(setMatches)
      .catch(() => {});
  }

  useEffect(() => {
    loadMatches();
  }, [onlyFavs]);

  async function handleRunMatching() {
    setRunning(true);
    try {
      const res = await api.runMatchingEngine();
      setMatches(onlyFavs ? res.filter((m) => m.is_favorite_company) : res);
    } finally {
      setRunning(false);
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">Vagas Recomendadas · Motor de Aderência</h1>
            <p className="text-sm text-slate-600">
              Pontuação explicável de 0 a 100 baseada em evidências. Não representa probabilidade de contratação.
            </p>
          </div>
          <button
            type="button"
            onClick={handleRunMatching}
            disabled={running}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
          >
            <Play className="h-4 w-4" />
            {running ? "Analisando..." : "Recalcular aderência"}
          </button>
        </div>

        <label className="inline-flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
          <input
            type="checkbox"
            checked={onlyFavs}
            onChange={(e) => setOnlyFavs(e.target.checked)}
          />
          Mostrar apenas empresas favoritas
        </label>

        {matches.length === 0 ? (
          <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-sm text-slate-500">
            Nenhuma análise executada ainda. Adicione vagas no Radar de Vagas e clique em{" "}
            <strong>Recalcular aderência</strong>.
          </div>
        ) : (
          <div className="space-y-4">
            {matches.map((m) => {
              const badge = CLASSIFICATION_LABEL[m.classification] || CLASSIFICATION_LABEL.baixa_prioridade;
              return (
                <div
                  key={m.id}
                  className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-base font-bold text-slate-900">{m.job_title}</span>
                        <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${badge.cls}`}>
                          {badge.text}
                        </span>
                        {m.is_favorite_company && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 text-xs font-semibold border border-amber-200">
                            <Star className="h-3 w-3 fill-amber-500 text-amber-500" />
                            Favorita
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {m.company_name}
                        {m.modality && ` · ${m.modality}`}
                        {m.seniority && ` · ${m.seniority}`}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="text-2xl font-extrabold text-indigo-700">
                          {m.total_score.toFixed(0)}
                          <span className="text-xs font-normal text-slate-500">/100</span>
                        </div>
                        <div className="text-[11px] text-slate-500">
                          Prioridade: {m.priority_score.toFixed(0)}
                        </div>
                      </div>
                      {m.is_eligible && (
                        <button
                          type="button"
                          onClick={() => handlePrepareApplication(m.job_posting_id)}
                          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700"
                        >
                          <Send className="h-3.5 w-3.5" /> Preparar
                        </button>
                      )}
                      <a
                        href={m.original_url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                  </div>

                  {/* Dimensions */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 text-xs">
                    {Object.entries(m.dimension_scores).map(([k, val]) => (
                      <div key={k} className="p-2 rounded-lg bg-slate-50 border border-slate-200">
                        <div className="text-[10px] text-slate-500 truncate">{k.replace(/_/g, " ")}</div>
                        <div className="font-bold text-slate-900">{val} pts</div>
                      </div>
                    ))}
                  </div>

                  {m.explanation.eliminatory_flags.length > 0 && (
                    <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 space-y-1">
                      <div className="font-semibold flex items-center gap-1.5">
                        <AlertTriangle className="h-3.5 w-3.5" />
                        Critérios eliminatórios
                      </div>
                      {m.explanation.eliminatory_flags.map((f, idx) => (
                        <div key={idx}>• {f}</div>
                      ))}
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-emerald-50/50 border border-emerald-100">
                      <div className="font-semibold text-emerald-800 flex items-center gap-1.5 mb-1">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Evidências verificáveis
                      </div>
                      {m.explanation.verifiable_evidence.length === 0 ? (
                        <p className="text-slate-500">Nenhuma evidência direta encontrada.</p>
                      ) : (
                        <ul className="space-y-0.5 text-emerald-900">
                          {m.explanation.verifiable_evidence.map((ev, idx) => (
                            <li key={idx}>• {ev}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                      <div className="font-semibold text-slate-800 mb-1">Lacunas e recomendação</div>
                      <p className="text-slate-700 font-medium">{m.explanation.recommendation}</p>
                      {m.explanation.gaps.slice(0, 3).map((g, idx) => (
                        <div key={idx} className="text-slate-600 mt-0.5">
                          • {g}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}

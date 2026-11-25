"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, FileText, FileUp, Trash2 } from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, ApiError, ResumeItem } from "@/lib/api";

export default function ResumesPage() {
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listResumes().then(setResumes);
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadResume(file);
      const list = await api.listResumes();
      setResumes(list);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao enviar currículo.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: string) {
    setError(null);
    try {
      await api.deleteResume(id);
      const list = await api.listResumes();
      setResumes(list);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao excluir currículo.");
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Currículos</h1>
          <p className="text-sm text-slate-600">
            Gerencie o currículo anexado na base. Para enviar um novo arquivo, exclua o atual.
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">
            {error}
          </div>
        )}

        {resumes.length === 0 ? (
          <label className="flex flex-col items-center justify-center bg-white border-2 border-dashed border-slate-300 rounded-2xl p-8 cursor-pointer hover:border-indigo-500 transition">
            <FileUp className="h-8 w-8 text-indigo-600 mb-2" />
            <span className="text-sm font-semibold text-slate-700">
              {uploading ? "Processando arquivo..." : "Enviar currículo (PDF ou DOCX)"}
            </span>
            <input type="file" accept=".pdf,.docx" onChange={handleUpload} className="hidden" />
          </label>
        ) : (
          <div className="space-y-4">
            {resumes.length > 1 && (
              <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>
                  Existem <strong>{resumes.length} currículos</strong> na sua base. Exclua os
                  antigos para evitar duplicidade.
                </span>
              </div>
            )}

            {resumes.map((r) => (
              <div key={r.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 font-semibold text-sm">
                    <FileText className="h-4 w-4 text-indigo-600" />
                    {r.original_filename}
                    {r.is_primary && (
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700">
                        Principal
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-500 uppercase">
                      {r.file_format} · {(r.file_size_bytes / 1024).toFixed(1)} KB
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDelete(r.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition"
                      title="Excluir currículo"
                      aria-label="Excluir currículo"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {r.ambiguities_json.length > 0 && (
                  <div className="mt-3 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 space-y-1">
                    <div className="font-semibold flex items-center gap-1.5">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Pontos ambíguos detectados ({r.ambiguities_json.length})
                    </div>
                    {r.ambiguities_json.map((a, idx) => (
                      <div key={idx}>
                        • {a.message} {a.excerpt && <span className="italic">({a.excerpt})</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}

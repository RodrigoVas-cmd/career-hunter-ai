"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Sparkles } from "lucide-react";
import { api, ApiError, setToken } from "@/lib/api";

function AuthForm() {
  const router = useRouter();
  const params = useSearchParams();
  const initialMode = params.get("mode") === "register" ? "register" : "login";

  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res =
        mode === "register"
          ? await api.register({ email, password, full_name: fullName })
          : await api.login({ email, password });

      setToken(res.access_token);
      router.push(res.onboarding_completed ? "/app" : "/onboarding");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Não foi possível conectar ao servidor. Verifique se o backend está ativo.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg text-slate-900">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
            <Sparkles className="h-4 w-4" />
          </span>
          Career Hunter AI
        </Link>

        <h1 className="mt-6 text-2xl font-bold text-slate-900">
          {mode === "register" ? "Criar sua conta" : "Acessar sua conta"}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {mode === "register"
            ? "Seus dados ficam isolados e protegidos desde o primeiro acesso."
            : "Entre para acompanhar seu perfil verificado, cargos-alvo e empresas."}
        </p>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {mode === "register" && (
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Nome completo
              </label>
              <input
                type="text"
                required
                minLength={2}
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ex.: Ana Paula Ferreira"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-600 focus:outline-none"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700">
              E-mail profissional
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="voce@exemplo.com"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-600 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">
              Senha
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mínimo de 8 caracteres"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-600 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition"
          >
            {loading
              ? "Processando..."
              : mode === "register"
              ? "Criar conta e iniciar onboarding"
              : "Entrar"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-600">
          {mode === "register" ? (
            <>
              Já possui conta?{" "}
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setMode("login");
                }}
                className="font-semibold text-indigo-600 hover:underline"
              >
                Entrar
              </button>
            </>
          ) : (
            <>
              Ainda não tem conta?{" "}
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setMode("register");
                }}
                className="font-semibold text-indigo-600 hover:underline"
              >
                Criar conta gratuita
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AuthPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-50" />}>
      <AuthForm />
    </Suspense>
  );
}

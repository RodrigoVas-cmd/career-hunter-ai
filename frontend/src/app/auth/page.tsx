"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Sparkles } from "lucide-react";
import { api, ApiError, setToken } from "@/lib/api";

function AuthForm() {
  const router = useRouter();
  const params = useSearchParams();
  const modeParam = params.get("mode");
  const tokenParam = params.get("token") || "";
  const initialMode =
    modeParam === "register"
      ? "register"
      : modeParam === "forgot"
      ? "forgot"
      : modeParam === "reset"
      ? "reset"
      : "login";

  const [mode, setMode] = useState<"login" | "register" | "forgot" | "reset">(initialMode);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [resetToken, setResetToken] = useState(tokenParam);
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setInfoMsg(null);
    setLoading(true);
    try {
      if (mode === "forgot") {
        const res = await api.forgotPassword(email);
        if (res.dev_reset_token) {
          setResetToken(res.dev_reset_token);
          setMode("reset");
          setInfoMsg("Token de redefinição gerado. Defina sua nova senha abaixo.");
        } else {
          setInfoMsg(res.message);
        }
        return;
      }

      if (mode === "reset") {
        const res = await api.resetPassword(resetToken, newPassword);
        setInfoMsg(res.message);
        setPassword("");
        setNewPassword("");
        setMode("login");
        return;
      }

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
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-[#5035f5] text-white">
            <Sparkles className="h-4 w-4" />
          </span>
          Career Hunter AI
        </Link>

        <h1 className="mt-6 text-2xl font-bold text-slate-900">
          {mode === "register"
            ? "Criar sua conta"
            : mode === "forgot"
            ? "Recuperar senha"
            : mode === "reset"
            ? "Definir nova senha"
            : "Acessar sua conta"}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {mode === "register"
            ? "Seus dados ficam isolados e protegidos desde o primeiro acesso."
            : mode === "forgot"
            ? "Informe seu e-mail cadastrado para receber as instruções de redefinição."
            : mode === "reset"
            ? "Escolha uma nova senha com pelo menos 8 caracteres."
            : "Entre para acompanhar seu perfil verificado, cargos-alvo e empresas."}
        </p>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
            {error}
          </div>
        )}
        {infoMsg && (
          <div className="mt-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-sm text-emerald-800">
            {infoMsg}
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
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-[#5035f5] focus:outline-none"
              />
            </div>
          )}

          {(mode === "login" || mode === "register" || mode === "forgot") && (
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
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-[#5035f5] focus:outline-none"
              />
            </div>
          )}

          {(mode === "login" || mode === "register") && (
            <div>
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-slate-700">
                  Senha
                </label>
                {mode === "login" && (
                  <button
                    type="button"
                    onClick={() => {
                      setError(null);
                      setInfoMsg(null);
                      setMode("forgot");
                    }}
                    className="text-xs font-semibold text-[#5035f5] hover:underline"
                  >
                    Esqueci minha senha
                  </button>
                )}
              </div>
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mínimo de 8 caracteres"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-[#5035f5] focus:outline-none"
              />
            </div>
          )}

          {mode === "reset" && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Código / Token de redefinição
                </label>
                <input
                  type="text"
                  required
                  value={resetToken}
                  onChange={(e) => setResetToken(e.target.value)}
                  placeholder="Cole o token recebido"
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-[#5035f5] focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Nova senha
                </label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Mínimo de 8 caracteres"
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-[#5035f5] focus:outline-none"
                />
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-[#5035f5] text-white text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition"
          >
            {loading
              ? "Processando..."
              : mode === "register"
              ? "Criar conta e iniciar onboarding"
              : mode === "forgot"
              ? "Enviar link de redefinição"
              : mode === "reset"
              ? "Salvar nova senha"
              : "Entrar"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-600">
          {mode === "register" || mode === "forgot" || mode === "reset" ? (
            <>
              {mode === "register" ? "Já possui conta? " : "Lembrou a senha? "}
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setInfoMsg(null);
                  setMode("login");
                }}
                className="font-semibold text-[#5035f5] hover:underline"
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
                  setInfoMsg(null);
                  setMode("register");
                }}
                className="font-semibold text-[#5035f5] hover:underline"
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

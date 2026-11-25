"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, Sparkles } from "lucide-react";
import { adminApi, AdminApiError, setAdminToken } from "@/lib/api";

export default function AdminLoginPage() {
  const router = useRouter();
  const [hasSuperadmin, setHasSuperadmin] = useState<boolean | null>(null);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [bootstrapToken, setBootstrapToken] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [mfaRequired, setMfaRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    adminApi
      .bootstrapStatus()
      .then((res) => setHasSuperadmin(res.has_superadmin))
      .catch(() => setHasSuperadmin(true));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (hasSuperadmin === false) {
        const res = await adminApi.bootstrap({
          email,
          full_name: fullName,
          password,
          bootstrap_token: bootstrapToken || undefined,
        });
        setAdminToken(res.access_token);
        router.push("/admin");
        return;
      }

      const res = await adminApi.login({
        email,
        password,
        totp_code: mfaRequired ? totpCode : undefined,
      });
      if (res.mfa_required) {
        setMfaRequired(true);
        return;
      }
      if (res.access_token) {
        setAdminToken(res.access_token);
        router.push("/admin");
      }
    } catch (err) {
      setError(
        err instanceof AdminApiError
          ? err.message
          : "Não foi possível conectar à API administrativa (porta 8001)."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f5f7fa] px-4">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
        <div className="flex items-center gap-2.5">
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-[#5035f5] text-white">
            <Sparkles className="h-4 w-4" />
          </span>
          <div>
            <div className="font-bold text-base text-[#10172a]">Career Hunter AI</div>
            <div className="text-xs text-slate-500">Admin Control Center</div>
          </div>
        </div>

        <h1 className="mt-6 text-xl font-bold text-[#10172a]">
          {hasSuperadmin === false
            ? "Bootstrap do Primeiro Superadministrador"
            : "Acesso Administrativo"}
        </h1>
        <p className="mt-1 text-xs text-slate-600 flex items-center gap-1.5">
          <ShieldCheck className="h-4 w-4 text-[#5035f5] shrink-0" />
          Ambiente isolado com verificação RBAC e auditoria no servidor.
        </p>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {hasSuperadmin === false && (
            <div>
              <label className="block text-xs font-semibold text-slate-700">Nome completo</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700">E-mail administrativo</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700">Senha</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
            />
          </div>

          {hasSuperadmin === false && (
            <div>
              <label className="block text-xs font-semibold text-slate-700">
                Token de Bootstrap (obrigatório em produção)
              </label>
              <input
                type="password"
                value={bootstrapToken}
                onChange={(e) => setBootstrapToken(e.target.value)}
                placeholder="ADMIN_BOOTSTRAP_TOKEN"
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          )}

          {mfaRequired && (
            <div>
              <label className="block text-xs font-semibold text-slate-700">
                Código MFA (6 dígitos)
              </label>
              <input
                type="text"
                required
                maxLength={6}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-[#5035f5] text-white text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading
              ? "Validando..."
              : hasSuperadmin === false
              ? "Criar Superadministrador e Entrar"
              : "Entrar no Control Center"}
          </button>
        </form>
      </div>
    </div>
  );
}

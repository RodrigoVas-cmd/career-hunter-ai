"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Download, MoreHorizontal, Search } from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { adminApi, AdminUserRow, getAdminToken } from "@/lib/api";

export default function UsersManagementPage() {
  const [items, setItems] = useState<AdminUserRow[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [plan, setPlan] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [modality, setModality] = useState("all");
  const [page, setPage] = useState(1);

  function load() {
    adminApi
      .listUsers({ q, plan, status_filter: statusFilter, modality, page })
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
      })
      .catch(() => {});
  }

  useEffect(() => {
    load();
  }, [plan, statusFilter, modality, page]);

  async function handleExportCsv() {
    const just = window.prompt("Informe a justificativa para exportar a lista de usuários (auditado):");
    if (!just || just.trim().length < 5) return;
    const token = getAdminToken();
    const res = await fetch(
      `${adminApi.baseUrl}/users/export-csv?justification=${encodeURIComponent(just.trim())}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} }
    );
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "usuarios_career_hunter.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <AdminShell>
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-[#10172a]">Gerenciamento de usuários</h1>
            <p className="text-xs text-slate-500">{total} usuário(s) encontrado(s)</p>
          </div>
          <button
            type="button"
            onClick={handleExportCsv}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <Download className="h-3.5 w-3.5" /> Exportar CSV
          </button>
        </div>

        {/* Search & Filters (PDF Ref 02) */}
        <div className="flex flex-wrap gap-3 items-center">
          <div className="flex-1 min-w-[220px] flex gap-2">
            <input
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && load()}
              placeholder="Buscar por nome, e-mail ou ID..."
              className="flex-1 rounded-xl border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              type="button"
              onClick={() => {
                setPage(1);
                load();
              }}
              className="px-3.5 py-2 rounded-xl bg-[#5035f5] text-white"
            >
              <Search className="h-4 w-4" />
            </button>
          </div>

          <select
            value={plan}
            onChange={(e) => setPlan(e.target.value)}
            className="rounded-xl border border-slate-300 px-3 py-2 text-xs font-semibold text-[#5035f5]"
          >
            <option value="all">Todos os planos</option>
            <option value="free">Free</option>
            <option value="pro">Pro</option>
            <option value="premium">Premium</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-xl border border-slate-300 px-3 py-2 text-xs font-semibold text-[#5035f5]"
          >
            <option value="all">Status da conta</option>
            <option value="active">Ativo</option>
            <option value="suspended">Suspenso</option>
            <option value="deactivated">Desativado</option>
          </select>

          <select
            value={modality}
            onChange={(e) => setModality(e.target.value)}
            className="rounded-xl border border-slate-300 px-3 py-2 text-xs font-semibold text-[#5035f5]"
          >
            <option value="all">Modalidade</option>
            <option value="paid">Pagante</option>
            <option value="courtesy">Cortesia</option>
            <option value="free">Free</option>
            <option value="unclassified">Não classificado</option>
          </select>
        </div>

        {/* Table (PDF Ref 02) */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-bold text-slate-600">
                <th className="py-3 pr-4">Usuário</th>
                <th className="py-3 px-4">Plano</th>
                <th className="py-3 px-4">Modalidade</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Cadastro</th>
                <th className="py-3 pl-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-xs text-slate-500">
                    Nenhum usuário encontrado com os filtros atuais.
                  </td>
                </tr>
              ) : (
                items.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/80">
                    <td className="py-3 pr-4">
                      <Link href={`/admin/usuarios/${u.id}`} className="font-semibold text-[#10172a] hover:text-[#5035f5]">
                        {u.full_name}
                      </Link>
                      <div className="text-xs text-slate-500">{u.email}</div>
                    </td>
                    <td className="py-3 px-4 text-xs font-semibold text-[#5035f5]">
                      {u.plan_name}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-600 capitalize">
                      {u.access_modality === "unclassified" ? "Não classificado" : u.access_modality}
                    </td>
                    <td className="py-3 px-4 text-xs">
                      <span
                        className={`font-semibold ${
                          u.account_status === "active"
                            ? "text-emerald-600"
                            : u.account_status === "suspended"
                            ? "text-amber-600"
                            : "text-red-600"
                        }`}
                      >
                        {u.account_status === "active"
                          ? "Ativo"
                          : u.account_status === "suspended"
                          ? "Suspenso"
                          : "Desativado"}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-600">
                      {new Date(u.created_at).toLocaleDateString("pt-BR")}
                    </td>
                    <td className="py-3 pl-4 text-right">
                      <Link
                        href={`/admin/usuarios/${u.id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-200 text-xs font-semibold text-[#5035f5] hover:bg-indigo-50"
                      >
                        <MoreHorizontal className="h-3.5 w-3.5" /> Ficha
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AdminShell>
  );
}

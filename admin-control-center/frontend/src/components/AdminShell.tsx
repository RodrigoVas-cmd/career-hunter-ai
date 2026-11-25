"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  Bot,
  ChevronLeft,
  ChevronRight,
  Cpu,
  CreditCard,
  DollarSign,
  Gift,
  LayoutDashboard,
  LifeBuoy,
  LogOut,
  Menu,
  Search,
  Settings,
  ShieldAlert,
  Sliders,
  Sparkles,
  TrendingUp,
  Users,
  X,
} from "lucide-react";
import { adminApi, AdminMe, clearAdminToken, getAdminToken } from "@/lib/api";

const NAV = [
  { label: "Visão Geral", href: "/admin", icon: LayoutDashboard },
  { label: "Usuários", href: "/admin/usuarios", icon: Users },
  { label: "Assinaturas", href: "/admin/assinaturas", icon: CreditCard },
  { label: "Financeiro", href: "/admin/rentabilidade", icon: DollarSign },
  { label: "Planos e Limites", href: "/admin/planos", icon: Sliders },
  { label: "Inteligência Artificial", href: "/admin/ia", icon: Cpu },
  { label: "Monitoramento de Buscas", href: "/admin/buscas", icon: Search },
  { label: "Inteligência Comercial", href: "/admin/comercial", icon: TrendingUp },
  { label: "Cupons e Cortesias", href: "/admin/cupons", icon: Gift },
  { label: "Agentes e Prompts", href: "/admin/prompts", icon: Bot },
  { label: "Suporte", href: "/admin/suporte", icon: LifeBuoy },
  { label: "Auditoria e Segurança", href: "/admin/auditoria", icon: ShieldAlert },
  { label: "Configurações", href: "/admin/configuracoes", icon: Settings },
];

export default function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [admin, setAdmin] = useState<AdminMe | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const token = getAdminToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    adminApi
      .me()
      .then(setAdmin)
      .catch(() => {
        clearAdminToken();
        router.replace("/login");
      });
  }, [router]);

  function handleLogout() {
    clearAdminToken();
    router.push("/login");
  }

  if (!admin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f5f7fa] text-sm text-slate-600">
        Verificando sessão administrativa...
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-[#f5f7fa] text-[#10172a]">
      {/* Desktop Sidebar */}
      <aside
        className={`hidden lg:flex flex-col bg-[#10172a] text-white border-r border-slate-800 transition-all ${
          collapsed ? "w-20" : "w-64"
        } shrink-0`}
      >
        <div className="h-16 px-4 flex items-center justify-between border-b border-slate-800">
          <Link href="/admin" className="flex items-center gap-2.5 overflow-hidden">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-[#5035f5] text-white shrink-0">
              <Sparkles className="h-4 w-4" />
            </span>
            {!collapsed && (
              <div className="leading-tight truncate">
                <div className="font-bold text-sm">Career Hunter AI</div>
                <div className="text-[11px] text-slate-400">Admin Control Center</div>
              </div>
            )}
          </Link>
          <button
            type="button"
            onClick={() => setCollapsed((v) => !v)}
            className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white"
            title={collapsed ? "Expandir menu" : "Recolher menu"}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {NAV.map((item) => {
            const Icon = item.icon;
            const active =
              item.href === "/admin"
                ? pathname === "/admin"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                title={item.label}
                className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition ${
                  active
                    ? "bg-[#5035f5] text-white"
                    : "text-slate-300 hover:bg-slate-800/80 hover:text-white"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-slate-800 space-y-2">
          {!collapsed && (
            <div className="px-2">
              <div className="text-xs font-semibold truncate">{admin.full_name}</div>
              <div className="text-[11px] text-indigo-300 uppercase tracking-wider">
                {admin.admin_role}
              </div>
            </div>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <LogOut className="h-4 w-4 shrink-0" />
            {!collapsed && <span>Sair</span>}
          </button>
        </div>
      </aside>

      {/* Mobile Header + Drawer */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="lg:hidden h-14 bg-[#10172a] text-white px-4 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-sm">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-[#5035f5]">
              <Sparkles className="h-4 w-4" />
            </span>
            Admin Control Center
          </div>
          <button type="button" onClick={() => setMobileOpen((v) => !v)}>
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </header>

        {mobileOpen && (
          <div className="lg:hidden bg-[#10172a] text-white p-3 space-y-1 border-b border-slate-800">
            {NAV.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-slate-200 hover:bg-slate-800"
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
            <button
              type="button"
              onClick={handleLogout}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-red-300 hover:bg-slate-800"
            >
              <LogOut className="h-4 w-4" /> Sair
            </button>
          </div>
        )}

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

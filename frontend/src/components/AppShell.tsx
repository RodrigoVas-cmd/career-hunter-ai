"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  Bell,
  Briefcase,
  Building2,
  CreditCard,
  FileText,
  Kanban,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Radar,
  Send,
  Settings,
  Sparkles,
  Target,
  UserCheck,
  X,
} from "lucide-react";
import { api, clearToken, getToken, UserMe } from "@/lib/api";

const NAV_ITEMS = [
  { label: "Visão Geral", href: "/app", icon: LayoutDashboard },
  { label: "Meu Perfil", href: "/app/perfil", icon: UserCheck },
  { label: "Meus Cargos-Alvo", href: "/app/cargos", icon: Target },
  { label: "Minhas Empresas", href: "/app/empresas", icon: Building2 },
  { label: "Radar de Vagas", href: "/app/radar", icon: Radar },
  { label: "Vagas Recomendadas", href: "/app/recomendadas", icon: Briefcase },
  { label: "Currículos", href: "/app/curriculos", icon: FileText },
  { label: "Candidaturas", href: "/app/candidaturas", icon: Send },
  { label: "Pipeline", href: "/app/pipeline", icon: Kanban },
  { label: "Entrevistas", href: "/app/entrevistas", icon: MessageSquare },
  { label: "Relatórios", href: "/app/relatorios", icon: BarChart3 },
  { label: "Notificações", href: "/app/notificacoes", icon: Bell },
  { label: "Minha Assinatura", href: "/app/assinatura", icon: CreditCard },
  { label: "Configurações", href: "/app/configuracoes", icon: Settings },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<UserMe | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/auth?mode=login");
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => {
        clearToken();
        router.replace("/auth?mode=login");
      });
  }, [router]);

  function handleLogout() {
    clearToken();
    router.push("/auth?mode=login");
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-sm text-slate-600">
        Carregando sessão segura...
      </div>
    );
  }

  const sidebarContent = (
    <div className="flex flex-col h-full">
      <div className="h-16 px-4 flex items-center justify-between border-b border-slate-200">
        <Link href="/app" className="flex items-center gap-2 font-bold text-slate-900">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
            <Sparkles className="h-4 w-4" />
          </span>
          <span className="text-sm">Career Hunter AI</span>
        </Link>
        <button
          type="button"
          className="lg:hidden p-1 text-slate-500"
          onClick={() => setMobileOpen(false)}
          aria-label="Fechar menu"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition ${
                active
                  ? "bg-indigo-50 text-indigo-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-slate-200 space-y-2">
        {!user.onboarding_completed && (
          <Link
            href="/onboarding"
            className="block w-full text-center px-3 py-2 rounded-lg bg-amber-50 border border-amber-200 text-xs font-semibold text-amber-800 hover:bg-amber-100"
          >
            Continuar Onboarding (Etapa {user.onboarding_step}/6)
          </Link>
        )}
        <div className="px-2 py-1">
          <p className="text-xs font-semibold text-slate-900 truncate">{user.full_name}</p>
          <p className="text-xs text-slate-500 truncate">{user.email}</p>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-600 hover:bg-slate-100 hover:text-red-600 transition"
        >
          <LogOut className="h-4 w-4" />
          Sair
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:block w-64 bg-white border-r border-slate-200 shrink-0">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-slate-900/40"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="relative w-64 max-w-full bg-white h-full shadow-xl z-10">
            {sidebarContent}
          </aside>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="lg:hidden h-14 bg-white border-b border-slate-200 px-4 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="p-1.5 rounded-lg text-slate-600 hover:bg-slate-100"
            aria-label="Abrir menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          <span className="font-bold text-sm text-slate-900">Career Hunter AI</span>
          <div className="w-8" />
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

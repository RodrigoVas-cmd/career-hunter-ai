"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Bell, CheckCircle2, ExternalLink } from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, NotificationItem } from "@/lib/api";

export default function NotificationsPage() {
  const [items, setItems] = useState<NotificationItem[]>([]);

  useEffect(() => {
    api.listNotifications().then(setItems).catch(() => {});
  }, []);

  async function markRead(id: string) {
    await api.markNotificationRead(id);
    setItems((prev) =>
      prev.map((it) => (it.id === id ? { ...it, is_read: true } : it))
    );
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Notificações</h1>
          <p className="text-sm text-slate-600">
            Alertas de integração, recomendações do sistema e atualizações da sua conta.
          </p>
        </div>

        <div className="space-y-3">
          {items.length === 0 ? (
            <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-sm text-slate-500">
              Nenhuma notificação no momento.
            </div>
          ) : (
            items.map((n) => {
              const isWarn = n.category === "warning";
              const isSuccess = n.category === "success";
              return (
                <div
                  key={n.id}
                  className={`p-5 rounded-2xl border shadow-sm space-y-2 ${
                    isWarn
                      ? "bg-amber-50 border-amber-200"
                      : isSuccess
                      ? "bg-emerald-50 border-emerald-200"
                      : "bg-white border-slate-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2 font-bold text-sm text-slate-900">
                      {isWarn ? (
                        <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
                      ) : isSuccess ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                      ) : (
                        <Bell className="h-4 w-4 text-indigo-600 shrink-0" />
                      )}
                      {n.title}
                    </div>
                    {!n.is_system_alert && !n.is_read && (
                      <button
                        type="button"
                        onClick={() => markRead(n.id)}
                        className="text-xs font-semibold text-indigo-600 hover:underline shrink-0"
                      >
                        Marcar como lida
                      </button>
                    )}
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed">{n.body}</p>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {n.action_url && (
                      <Link
                        href={n.action_url}
                        className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700"
                      >
                        Ir para Configurações
                      </Link>
                    )}
                    {n.external_guide_url && (
                      <a
                        href={n.external_guide_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Como gerar chave API na OpenAI <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </AppShell>
  );
}

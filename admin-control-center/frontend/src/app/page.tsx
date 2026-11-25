"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAdminToken } from "@/lib/api";

export default function AdminRootRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace(getAdminToken() ? "/admin" : "/login");
  }, [router]);
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f5f7fa] text-sm text-slate-500">
      Carregando Admin Control Center...
    </div>
  );
}

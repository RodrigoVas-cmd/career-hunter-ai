const ADMIN_API_BASE =
  process.env.NEXT_PUBLIC_ADMIN_API_URL || "http://127.0.0.1:8001/api/v1/admin";

const TOKEN_KEY = "ch_admin_token";

export function getAdminToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAdminToken(token: string): void {
  if (typeof window !== "undefined") localStorage.setItem(TOKEN_KEY, token);
}

export function clearAdminToken(): void {
  if (typeof window !== "undefined") localStorage.removeItem(TOKEN_KEY);
}

export class AdminApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function req<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAdminToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${ADMIN_API_BASE}${path}`, { ...options, headers });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new AdminApiError(
      res.status,
      typeof data?.detail === "string" ? data.detail : "Erro na API administrativa."
    );
  }
  return data as T;
}

export interface AdminMe {
  id: string;
  email: string;
  full_name: string;
  admin_role: "superadmin" | "ops_admin" | "support" | "finance";
  mfa_enabled: boolean;
}

export interface ExecutiveDashboard {
  period: { code: string; start: string; end: string };
  users: {
    total: number;
    free: number;
    pro: number;
    premium: number;
    active: number;
    suspended: number;
    deactivated: number;
    new_in_period: number;
    modalities: { free: number; paid: number; courtesy: number; unclassified: number };
    conversion_paid_pct: number;
  };
  financial: {
    verified_mrr_brl_cents: number;
    verified_arr_brl_cents: number;
    operational_costs_brl_cents: number;
    ai_cost_usd: number;
    total_tokens: number;
    has_ai_cost_telemetry: boolean;
    has_payment_provider: boolean;
    ticket_medio_brl_cents: number;
  };
  usage: {
    analyses: number;
    tailored_resumes: number;
    applications: number;
    active_jobs: number;
    monitored_companies: number;
    agent_runs: number;
  };
  evolution: Array<{ month: string; users: number }>;
}

export interface AdminUserRow {
  id: string;
  full_name: string;
  email: string;
  account_status: string;
  plan_code: string;
  plan_name: string;
  plan_price_brl_cents: number;
  access_modality: string;
  subscription_status: string;
  subscription_start: string | null;
  next_renewal: string | null;
  courtesy_expires_at: string | null;
  created_at: string;
}

export interface AdminUserDetail extends AdminUserRow {
  profile: {
    headline: string | null;
    city: string | null;
    state: string | null;
    phone: string | null;
    seniority_level: string | null;
    target_roles: string[];
    favorite_companies_count: number;
  };
  documents: {
    originals: Array<{
      id: string;
      name: string;
      format: string;
      parse_status: string;
      is_primary: boolean;
      created_at: string;
    }>;
    ats_versions: Array<{
      id: string;
      label: string;
      approved_by_user: boolean;
      has_pdf: boolean;
      has_docx: boolean;
      created_at: string;
    }>;
  };
  usage: {
    analyses_used: number;
    analyses_limit: number;
    extra_analysis_credits: number;
    custom_resumes_used: number;
    custom_resumes_limit: number;
    applications_used: number;
    applications_limit: number;
  };
  courtesy: {
    id: string;
    plan_code: string;
    duration_type: string;
    starts_at: string;
    expires_at: string | null;
    reason: string;
  } | null;
  history: Array<{
    source: string;
    action: string;
    justification: string | null;
    actor: string | null;
    created_at: string;
  }>;
}

export const adminApi = {
  baseUrl: ADMIN_API_BASE,
  bootstrapStatus: () => req<{ has_superadmin: boolean }>("/auth/bootstrap-status"),
  bootstrap: (payload: {
    email: string;
    full_name: string;
    password: string;
    bootstrap_token?: string;
  }) => req<{ access_token: string; admin: AdminMe }>("/auth/bootstrap", {
    method: "POST",
    body: JSON.stringify(payload),
  }),
  login: (payload: { email: string; password: string; totp_code?: string }) =>
    req<{ mfa_required: boolean; access_token: string | null; admin?: AdminMe }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  me: () => req<AdminMe>("/auth/me"),
  getDashboard: (period = "30d") =>
    req<ExecutiveDashboard>(`/dashboard/executive?period=${encodeURIComponent(period)}`),
  listUsers: (params: {
    q?: string;
    plan?: string;
    status_filter?: string;
    modality?: string;
    page?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params.q) qs.set("q", params.q);
    if (params.plan && params.plan !== "all") qs.set("plan", params.plan);
    if (params.status_filter && params.status_filter !== "all")
      qs.set("status_filter", params.status_filter);
    if (params.modality && params.modality !== "all") qs.set("modality", params.modality);
    qs.set("page", String(params.page || 1));
    return req<{ total: number; page: number; page_size: number; items: AdminUserRow[] }>(
      `/users?${qs.toString()}`
    );
  },
  getUserDetail: (id: string) => req<AdminUserDetail>(`/users/${id}`),
  managePlan: (id: string, payload: Record<string, unknown>) =>
    req<{ status: string }>(`/users/${id}/manage-plan`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateUserStatus: (id: string, payload: { action: string; justification: string }) =>
    req<{ id: string; is_active: boolean; account_status: string }>(`/users/${id}/status`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  lgpdDeleteUser: (id: string, payload: { confirmation_text: string; justification: string }) =>
    req<{ status: string }>(`/users/${id}`, {
      method: "DELETE",
      body: JSON.stringify(payload),
    }),
  listPlans: () =>
    req<
      Array<{
        id: string;
        code: string;
        name: string;
        price_brl_cents: number;
        is_active: boolean;
        active_subscribers_count: number;
        features: Record<string, number | null>;
      }>
    >("/commercial/plans"),
  updatePlan: (code: string, payload: Record<string, unknown>) =>
    req<{ code: string; impacted_users: number }>(`/commercial/plans/${code}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  getProfitability: () =>
    req<{
      plans: Array<{
        plan_code: string;
        plan_name: string;
        price_brl_cents: number;
        paying_users: number;
        courtesy_users: number;
        unclassified_users: number;
        verified_revenue_brl_cents: number;
        ai_cost_usd: number;
      }>;
      operational_costs: Array<{
        id: string;
        category: string;
        provider_name: string;
        monthly_cost_brl_cents: number;
      }>;
      total_operational_costs_brl_cents: number;
      note: string;
    }>("/commercial/profitability"),
  listSubscriptions: () =>
    req<{ has_payment_provider: boolean; items: Array<Record<string, unknown>> }>(
      "/commercial/subscriptions"
    ),
  listCourtesies: () => req<Array<Record<string, unknown>>>("/commercial/courtesies"),
  listCoupons: () => req<Array<Record<string, unknown>>>("/commercial/coupons"),
  getAiCenter: () => req<Record<string, unknown>>("/ops/ai-center"),
  getSearches: () => req<Record<string, unknown>>("/ops/searches"),
  listPrompts: () => req<Array<Record<string, unknown>>>("/ops/prompts"),
  listSupport: () => req<Array<Record<string, unknown>>>("/ops/support"),
  listAuditLogs: () => req<Array<Record<string, unknown>>>("/ops/audit-logs"),
};

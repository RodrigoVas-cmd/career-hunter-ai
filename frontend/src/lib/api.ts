const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const TOKEN_KEY = "career_hunter_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function clearToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  isMultipart = false
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (!isMultipart) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...headers,
      ...(options.headers as Record<string, string> | undefined),
    },
  });

  if (res.status === 204) {
    return undefined as T;
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg =
      typeof data?.detail === "string"
        ? data.detail
        : "Erro ao processar requisição.";
    throw new ApiError(res.status, msg);
  }
  return data as T;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  onboarding_step: number;
  onboarding_completed: boolean;
}

export interface UserMe {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  onboarding_step: number;
  onboarding_completed: boolean;
}

export interface UserProfile {
  id: string;
  user_id: string;
  headline: string | null;
  summary: string | null;
  contact_email: string | null;
  phone: string | null;
  city: string | null;
  state: string | null;
  country: string;
  seniority_level: string | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
}

export interface Experience {
  id: string;
  user_id: string;
  company_name: string;
  role_title: string;
  raw_period_text: string | null;
  is_current: boolean;
  responsibilities: string | null;
  proven_results: string | null;
  leadership_experience: boolean;
  sector: string | null;
  origin: string;
  evidence_excerpt: string | null;
  validation_status: string;
  ambiguity_note: string | null;
}

export interface Skill {
  id: string;
  user_id: string;
  name: string;
  category: string;
  proficiency: string | null;
  years_experience: number | null;
  origin: string;
  evidence_excerpt: string | null;
  validation_status: string;
  ambiguity_note: string | null;
}

export interface ResumeItem {
  id: string;
  user_id: string;
  original_filename: string;
  file_format: string;
  file_size_bytes: number;
  extracted_data_json: Record<string, unknown>;
  ambiguities_json: Array<{ field: string; message: string; excerpt: string }>;
  parse_status: string;
  is_primary: boolean;
  created_at: string;
}

export interface TargetRole {
  id: string;
  user_id: string;
  title: string;
  desired_seniority: string | null;
  area: string | null;
  priority: "alta" | "media" | "baixa";
  synonyms: string[];
  desired_sectors: string[];
  min_salary_brl: number | null;
  desired_salary_brl: number | null;
  locations: string[];
  modalities: string[];
  mandatory_criteria: string[];
  status: "ativo" | "pausado";
}

export interface TargetRoleSuggestion {
  title: string;
  justification: string;
  based_on_evidence: string;
  synonyms: string[];
}

export interface FavoriteCompany {
  id: string;
  user_id: string;
  company_id: string;
  priority: "alta" | "media" | "baixa";
  roles_of_interest: string[];
  departments: string[];
  notes: string | null;
  monitoring_status: string;
  company: {
    id: string;
    name: string;
    official_website: string | null;
    careers_page_url: string | null;
    city: string | null;
    state: string | null;
    country: string;
    sector: string | null;
  };
}

export interface CareerPreference {
  id: string;
  user_id: string;
  current_city: string | null;
  current_state: string | null;
  desired_locations: string[];
  work_modalities: string[];
  max_commute_minutes: number | null;
  max_commute_km: number | null;
  relocation_available: boolean | null;
  travel_available: boolean | null;
  min_salary_brl: number | null;
  desired_salary_brl: number | null;
  salary_negotiable: boolean;
  contract_types: string[];
  excluded_companies: string[];
  preferred_sectors: string[];
  professional_restrictions: string | null;
  application_languages: string[];
  search_frequency_hours: number;
  monitoring_windows: string[];
  max_recommended_jobs: number;
  min_match_score: number;
  eliminatory_criteria: string[];
  prioritize_favorite_companies: boolean;
  application_mode: string;
  has_openai_key?: boolean;
  openai_api_key?: string;
}

export interface PlanStatus {
  plan_code: "free" | "pro" | "premium" | string;
  plan_name: string;
  price_brl_cents: number;
  monthly_analyses_limit: number;
  monthly_analyses_used: number;
  monthly_analyses_remaining: number;
  resets_at: string;
  features: Record<string, number | null>;
}

export interface DashboardSummary {
  user: {
    id: string;
    full_name: string;
    onboarding_step: number;
    onboarding_completed: boolean;
  };
  plan?: PlanStatus;
  counts: {
    resumes: number;
    experiences: number;
    verified_experiences: number;
    skills: number;
    target_roles: number;
    favorite_companies: number;
    discovered_jobs?: number;
    compatible_jobs?: number;
    applications: number;
    sent_applications?: number;
    pending_applications?: number;
    interview_applications?: number;
    rejected_applications?: number;
    offer_applications?: number;
    unread_notifications: number;
  };
}

export interface JobPosting {
  id: string;
  company_name: string;
  title: string;
  description: string;
  original_url: string;
  location: string | null;
  modality: string | null;
  seniority: string | null;
  salary_range_text: string | null;
  availability_status: string;
  discovered_at: string;
  is_favorite_company: boolean;
}

export interface JobMatch {
  id: string;
  job_posting_id: string;
  company_name: string;
  job_title: string;
  original_url: string;
  location: string | null;
  modality: string | null;
  seniority: string | null;
  is_favorite_company: boolean;
  total_score: number;
  priority_score: number;
  classification: string;
  is_eligible: boolean;
  confidence_level: number;
  dimension_scores: Record<string, number>;
  explanation: {
    met_requirements: string[];
    partial_requirements: string[];
    unproven_requirements: string[];
    eliminatory_flags: string[];
    verifiable_evidence: string[];
    transferable_skills: string[];
    gaps: string[];
    justification: string;
    recommendation: string;
  };
}

export interface CompanyWatchResult {
  monitored_count: number;
  error_count: number;
  total_jobs_found: number;
  results: Array<{
    favorite_company_id: string;
    company_name: string;
    careers_page_url: string | null;
    status: string;
    jobs_found: number;
    error_message: string | null;
  }>;
}

export interface ResumeVersion {
  id: string;
  base_resume_id: string;
  job_posting_id: string | null;
  version_label: string;
  content_json: Record<string, unknown>;
  changes_summary_json: string[];
  approved_by_user: boolean;
  docx_path?: string | null;
  pdf_path?: string | null;
  created_at: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  body: string;
  category: string;
  is_read: boolean;
  is_system_alert: boolean;
  action_url?: string | null;
  external_guide_url?: string | null;
}

export interface ApplicationAnswer {
  id: string;
  application_id: string;
  question_text: string;
  question_category: string;
  draft_answer: string | null;
  approved_answer: string | null;
  evidence_refs_json: string[];
  requires_human_input: boolean;
}

export interface ApplicationEvent {
  id: string;
  event_type: string;
  description: string | null;
  occurred_at: string;
}

export interface InterviewItem {
  id: string;
  application_id: string;
  stage_name: string;
  scheduled_at: string | null;
  status: string;
  notes: string | null;
}

export interface ApplicationItem {
  id: string;
  job_posting_id: string | null;
  resume_version_id: string | null;
  company_name: string;
  role_title: string;
  operational_status: string;
  process_stage: string | null;
  source_url: string | null;
  is_manual: boolean;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
  has_valid_approval: boolean;
}

export interface ApplicationDetail extends ApplicationItem {
  resume_version: ResumeVersion | null;
  answers: ApplicationAnswer[];
  events: ApplicationEvent[];
  interviews: InterviewItem[];
}

export const api = {
  register: (payload: { email: string; password: string; full_name: string }) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  login: (payload: { email: string; password: string }) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  forgotPassword: (email: string) =>
    request<{
      email_sent: boolean;
      smtp_configured: boolean;
      message: string;
      dev_reset_token?: string;
    }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  resetPassword: (token: string, new_password: string) =>
    request<{ message: string }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password }),
    }),
  changePassword: (current_password: string, new_password: string) =>
    request<{ message: string }>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password, new_password }),
    }),
  me: () => request<UserMe>("/auth/me"),
  updateOnboarding: (onboarding_step: number, onboarding_completed?: boolean) =>
    request<UserMe>("/auth/me/onboarding", {
      method: "PATCH",
      body: JSON.stringify({ onboarding_step, onboarding_completed }),
    }),
  getDashboardSummary: () => request<DashboardSummary>("/dashboard/summary"),
  getProfile: () => request<UserProfile>("/profile"),
  updateProfile: (payload: Partial<UserProfile>) =>
    request<UserProfile>("/profile", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  listExperiences: () => request<Experience[]>("/profile/experiences"),
  createExperience: (payload: Partial<Experience>) =>
    request<Experience>("/profile/experiences", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateExperience: (id: string, payload: Partial<Experience>) =>
    request<Experience>(`/profile/experiences/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteExperience: (id: string) =>
    request<void>(`/profile/experiences/${id}`, { method: "DELETE" }),
  listSkills: () => request<Skill[]>("/profile/skills"),
  createSkill: (payload: Partial<Skill>) =>
    request<Skill>("/profile/skills", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateSkill: (id: string, payload: Partial<Skill>) =>
    request<Skill>(`/profile/skills/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteSkill: (id: string) =>
    request<void>(`/profile/skills/${id}`, { method: "DELETE" }),
  getPreferences: () => request<CareerPreference>("/profile/preferences"),
  updatePreferences: (payload: Partial<CareerPreference>) =>
    request<CareerPreference>("/profile/preferences", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  uploadResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ResumeItem>(
      "/resumes/upload",
      { method: "POST", body: form },
      true
    );
  },
  listResumes: () => request<ResumeItem[]>("/resumes"),
  deleteResume: (id: string) =>
    request<void>(`/resumes/${id}`, { method: "DELETE" }),
  compareWithLinkedin: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{
      matched_count: number;
      divergences: Array<{
        company_name: string;
        role_title: string | null;
        cv_period: string;
        linkedin_period: string;
        message: string;
      }>;
      only_in_cv: Array<{ company_name: string; role_title: string | null; period: string | null }>;
      only_in_linkedin: Array<{ company_name: string; role_title: string | null; period: string | null }>;
    }>("/resumes/compare-linkedin", { method: "POST", body: form }, true);
  },
  buildAdjustedResume: (setAsPrimary = true) =>
    request<ResumeItem>(`/resumes/build-adjusted?set_as_primary=${setAsPrimary}`, {
      method: "POST",
    }),
  previewAdjustedResume: () =>
    request<{
      content: {
        full_name: string;
        email: string;
        phone?: string | null;
        city?: string | null;
        state?: string | null;
        location?: string;
        linkedin_url?: string | null;
        summary?: string;
        skills: string[];
        experiences: Array<{
          company_name: string;
          role_title: string;
          sector?: string | null;
          raw_period_text?: string | null;
          responsibilities?: string | null;
          responsibilities_list?: string[];
          proven_results?: string | null;
        }>;
        education?: Array<{ raw?: string }>;
        languages?: Array<{ raw?: string }>;
      };
      changes_summary: string[];
    }>("/resumes/preview-adjusted"),
  getAtsSuggestions: () =>
    request<{
      ats_readiness_score: number;
      strengths: string[];
      suggestions: string[];
      actionable_options?: {
        suggested_skills: Array<{ name: string; evidence: string }>;
        suggested_summary: { text: string; evidence: string } | null;
      };
    }>("/resumes/ats-suggestions"),
  listTargetRoles: () => request<TargetRole[]>("/targeting/roles"),
  createTargetRole: (payload: Partial<TargetRole>) =>
    request<TargetRole>("/targeting/roles", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateTargetRole: (id: string, payload: Partial<TargetRole>) =>
    request<TargetRole>(`/targeting/roles/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteTargetRole: (id: string) =>
    request<void>(`/targeting/roles/${id}`, { method: "DELETE" }),
  getRoleSuggestions: () =>
    request<TargetRoleSuggestion[]>("/targeting/roles/suggestions"),
  listFavoriteCompanies: () =>
    request<FavoriteCompany[]>("/targeting/companies"),
  searchCompanyCatalog: (q: string, sector = "") => {
    const qs = new URLSearchParams();
    if (q) qs.set("q", q);
    if (sector) qs.set("sector", sector);
    return request<
      Array<{
        id: string;
        name: string;
        official_website: string | null;
        careers_page_url: string | null;
        city: string | null;
        state: string | null;
        country: string;
        sector: string | null;
      }>
    >(`/targeting/companies/catalog?${qs.toString()}`);
  },
  addFavoriteCompany: (payload: {
    name: string;
    official_website?: string;
    careers_page_url?: string;
    city?: string;
    state?: string;
    sector?: string;
    priority: "alta" | "media" | "baixa";
  }) =>
    request<FavoriteCompany>("/targeting/companies", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  importCompaniesCsv: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ imported_count: number; skipped_count: number; errors: string[] }>(
      "/targeting/companies/import-csv",
      { method: "POST", body: form },
      true
    );
  },
  deleteFavoriteCompany: (id: string) =>
    request<void>(`/targeting/companies/${id}`, { method: "DELETE" }),
  discoverAuto: () =>
    request<{
      created_count: number;
      updated_count: number;
      filtered_out_count: number;
      allows_remote: boolean;
      sources_checked: string[];
      matched_count: number;
    }>("/jobs/discover/auto", { method: "POST" }),
  discoverViaConnector: (payload: {
    source_kind: "greenhouse" | "lever" | "jsonld";
    target: string;
    company_name?: string;
  }) =>
    request<{
      source_kind: string;
      fetched_count: number;
      created_count: number;
      updated_count: number;
      jobs: JobPosting[];
    }>("/jobs/discover/connector", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createManualJob: (payload: {
    company_name: string;
    title: string;
    description: string;
    original_url: string;
    modality?: string;
    seniority?: string;
    location?: string;
  }) =>
    request<JobPosting>("/jobs/manual", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listJobs: (params?: {
    q?: string;
    modality?: string;
    only_favorites?: boolean;
    respect_preferences?: boolean;
  }) => {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.modality) qs.set("modality", params.modality);
    if (params?.only_favorites) qs.set("only_favorites", "true");
    if (params?.respect_preferences) qs.set("respect_preferences", "true");
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<JobPosting[]>(`/jobs${suffix}`);
  },
  deleteJob: (id: string) =>
    request<void>(`/jobs/${id}`, { method: "DELETE" }),
  runCompanyWatch: () =>
    request<CompanyWatchResult>("/jobs/company-watch/run", { method: "POST" }),
  runMatchingEngine: () =>
    request<JobMatch[]>("/jobs/matching/run", { method: "POST" }),
  listJobMatches: (params?: { only_favorites?: boolean; min_score?: number }) => {
    const qs = new URLSearchParams();
    if (params?.only_favorites) qs.set("only_favorites", "true");
    if (params?.min_score !== undefined) qs.set("min_score", String(params.min_score));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<JobMatch[]>(`/jobs/matches/list${suffix}`);
  },
  createApplication: (payload: {
    job_posting_id?: string;
    company_name?: string;
    role_title?: string;
    source_url?: string;
    is_manual?: boolean;
  }) =>
    request<ApplicationItem>("/applications", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listApplications: () => request<ApplicationItem[]>("/applications"),
  getApplicationDetail: (id: string) =>
    request<ApplicationDetail>(`/applications/${id}`),
  updateApplication: (
    id: string,
    payload: { operational_status?: string; process_stage?: string; note?: string }
  ) =>
    request<ApplicationItem>(`/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  generateAtsResume: (appId: string) =>
    request<ResumeVersion>(`/applications/${appId}/resume-version`, {
      method: "POST",
    }),
  approveAtsResume: (versionId: string) =>
    request<ResumeVersion>(`/applications/resume-versions/${versionId}/approve`, {
      method: "POST",
    }),
  prepareQuestion: (
    appId: string,
    payload: {
      question_text: string;
      field_type?: string;
      options?: string[];
      max_chars?: number;
    }
  ) =>
    request<ApplicationAnswer>(`/applications/${appId}/questions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  saveAnswer: (answerId: string, approved_answer: string) =>
    request<ApplicationAnswer>(`/applications/answers/${answerId}`, {
      method: "PATCH",
      body: JSON.stringify({ approved_answer }),
    }),
  approveApplication: (appId: string) =>
    request<{ id: string; is_valid: boolean }>(`/applications/${appId}/approve`, {
      method: "POST",
    }),
  confirmSubmission: (
    appId: string,
    payload: { confirmed?: boolean; ambiguous?: boolean; confirmation_note?: string }
  ) =>
    request<ApplicationItem>(`/applications/${appId}/confirm-submission`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createInterview: (
    appId: string,
    payload: { stage_name: string; scheduled_at?: string; notes?: string }
  ) =>
    request<InterviewItem>(`/applications/${appId}/interviews`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listAllInterviews: () =>
    request<InterviewItem[]>("/applications/interviews/all"),
  listNotifications: () => request<NotificationItem[]>("/notifications"),
  markNotificationRead: (id: string) =>
    request<void>(`/notifications/${id}/read`, { method: "PATCH" }),
};

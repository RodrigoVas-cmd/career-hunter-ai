# Career Hunter AI — Documento de Arquitetura

> **Versão:** 1.0 (Fundação SaaS — Fase 1)  
> **Diretório do projeto:** `c:\PROJETOS ANTIGRAVITY\carrier-hunter-ai`

---

## 1. Avaliação do Ambiente Disponível

Auditoria realizada na máquina local antes do início da implementação:

| Recurso | Status | Detalhes |
| :--- | :--- | :--- |
| **Node.js** | Disponível | `v26.13.0` (`npm.cmd` `11.20.0`) |
| **Python** | Disponível | `3.14.10` (`pip` `26.2.2`, `venv`, `sqlite3` `3.50.4`) |
| **Git** | Disponível | `2.56.1.windows.1` |
| **Docker / psql** | Indisponível | Não instalados localmente |
| **pnpm / uv** | Indisponível | Usar `npm.cmd` e `python -m venv` / `pip` |

**Decisão decorrente:** Como não há Docker/PostgreSQL local instalado, a camada de persistência será construída com **SQLAlchemy 2.0 + Alembic**, utilizando **PostgreSQL (ou Supabase com RLS)** como alvo de produção e **SQLite** como banco local padrão para desenvolvimento e testes automatizados imediatos, sem dependências externas bloqueantes.

---

## 2. Escolha e Justificativa da Stack

| Camada | Tecnologia | Justificativa |
| :--- | :--- | :--- |
| **Frontend** | Next.js (App Router), TypeScript, Tailwind CSS, Lucide React | SSR/SPA moderno, tipagem forte, estilização responsiva rápida, componentes acessíveis e suporte nativo a `pt-BR`. |
| **Backend** | Python 3.14, FastAPI, Pydantic v2, Uvicorn | Alta produtividade para APIs REST, validação rigorosa de schemas, excelente ecossistema para parsing de documentos (`pypdf`, `python-docx`) e orquestração de agentes de IA. |
| **Banco de Dados & Migrações** | SQLAlchemy 2.0, Alembic (SQLite dev / PostgreSQL prod) | Portabilidade direta entre SQLite local e PostgreSQL gerenciado; suporte a chaves estrangeiras, índices e isolamento por `user_id`. |
| **Autenticação & Segurança** | JWT (Access/Refresh), `passlib` / `argon2` ou `bcrypt`, CORS restrito | Sessões seguras, senhas com hash forte, isolamento multiusuário obrigatório em todas as rotas privadas. |
| **Testes** | `pytest` + `httpx` (Backend) / TypeScript `tsc` + lint (Frontend) | Verificação real de isolamento de dados, fluxos de autenticação, parsing e regras de negócio. |

---

## 3. Arquitetura Geral (Monólito Modular + Workers)

```text
┌──────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js + TS)                       │
│   Landing & Planos │ Onboarding (6 Etapas) │ App (14 Menus) │ Admin  │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │ HTTPS / JSON (Bearer JWT)
┌──────────────────────────────────▼───────────────────────────────────┐
│                      BACKEND API (FastAPI Modular)                   │
│  ┌───────────┐ ┌───────────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │   auth    │ │ users_profile │ │ resumes  │ │     targeting     │  │
│  └───────────┘ └───────────────┘ └──────────┘ └───────────────────┘  │
│  ┌───────────┐ ┌───────────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │ discovery │ │   matching    │ │   crm    │ │  billing & admin  │  │
│  └───────────┘ └───────────────┘ └──────────┘ └───────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │      Orquestrador Central & Agentes (A..L) + Filas/Workers     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │ SQLAlchemy 2.0
┌──────────────────────────────────▼───────────────────────────────────┐
│              BANCO DE DADOS (SQLite Dev / PostgreSQL Prod)           │
│     Dados Privados (isolados por user_id) │ Dados Públicos (Vagas)   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Módulos e Dependências

1. **`core`**: Configurações (`pydantic-settings`), banco de dados, segurança (JWT, hashing), logging estruturado sem credenciais, tratamento global de erros.
2. **`auth`**: Cadastro, login, recuperação de senha, verificação de sessão, separação de papéis (`user` vs `admin`). Depende de `core`.
3. **`users_profile`**: Perfil profissional, **Verified Professional Profile** (`professional_experiences`, `verified_skills`, `evidence_sources`), preferências de carreira (`career_preferences`). Depende de `auth`.
4. **`resumes`**: Upload privado (PDF/DOCX, validação de MIME/extensão/tamanho), extração estruturada de experiências/competências/formação/idiomas/certificações, sinalização de ambiguidades e fluxo de validação humana. Depende de `users_profile`.
5. **`targeting`**: Cargos-alvo (`target_roles` com senioridade, sinônimos, salário, status ativo/pausado) e Empresas Preferidas (`companies`, `favorite_companies`, importação CSV, `company_career_sources`). Depende de `auth`.
6. **`discovery`** *(Fase 2)*: Conectores independentes, normalização, deduplicação e `Company Watch` (`company_monitoring_runs`, `job_sources`, `job_postings`, `job_requirements`).
7. **`matching`** *(Fase 2)*: Motor de aderência explicável 0–100 com pesos configuráveis e bloqueio de eliminatórios (`job_matches`).
8. **`applications`** *(Fase 3)*: Personalização de currículo para ATS (`resume_versions`), respostas verificadas (`application_answers`), aprovação humana explícita (`application_approvals`), envio supervisionado e CRM (`applications`, `application_events`, `interviews`, `recruiter_messages`).
9. **`billing`** *(Fase 4)*: Planos configuráveis (Free, Pro, Premium), verificação de quotas no backend (`plans`, `plan_features`, `subscriptions`, `usage_events`, `billing_events`), adaptador de pagamentos recorrentes (BR) com webhooks idempotentes.
10. **`admin`** *(Fase 4)*: Painel administrativo agregado sem acesso padrão a currículos ou mensagens privadas dos clientes, com suporte auditável (`audit_logs`).
11. **`orchestrator`** *(Fases 2–5)*: Orquestrador central coordenando os Agentes A–L por eventos, demandas e agendamentos persistentes (`agent_runs`), com orçamento de tokens e proteção contra prompt injection.

---

## 5. Integrações Viáveis vs. Restrições Técnicas/Legais

Seguindo os princípios inegociáveis (nunca contornar CAPTCHA, login ou antifraude; respeitar Termos de Uso):

| Fonte | Viabilidade Inicial | Estratégia |
| :--- | :--- | :--- |
| **Greenhouse / Lever** | **Alta** | APIs públicas oficiais de Job Boards (`boards-api.greenhouse.io`, `api.lever.co`). |
| **Páginas Oficiais de Carreiras** | **Média/Alta** | Feeds RSS/Atom, sitemaps ou JSON-LD (`schema.org/JobPosting`) quando publicamente acessíveis. |
| **Importação CSV / Manual** | **Alta** | Cadastro direto de empresas e vagas pelo usuário. |
| **LinkedIn / Glassdoor / Indeed / Catho / Vagas.com.br / Gupy / Workday** | **Restrita** | Sem API pública aberta ou protegidas por login/antifraude. Não automatizar bypass; suportar apenas via integrações autorizadas, e-mails de alerta (Fase 5) ou conclusão manual assistida com link direto. |
| **E-mail (Gmail / Outlook)** | **Fase 5** | OAuth oficial com consentimento explícito e escopo mínimo somente leitura para acompanhamento. |
| **Pagamentos (Brasil)** | **Fase 4** | Adaptador agnóstico (compatível com Mercado Pago / Asaas / Stripe BR) com webhooks assinados. |

---

## 6. Segurança, Isolamento e Privacidade (LGPD)

- **Isolamento Multiusuário:** Toda tabela privada possui `user_id` indexado; todas as queries no backend filtram explicitamente pelo `current_user.id` extraído do JWT verificado.
- **Princípio da Não-Alucinação:** Toda informação extraída de currículo entra em `Verified Professional Profile` com `origin`, `evidence` e `validation_status` (`pending_review`, `verified`, `corrected`, `rejected`).
- **Proteção contra Prompt Injection:** Descrições de vagas e e-mails externos são tratados exclusivamente como dados não confiáveis.
- **Privacidade Administrativa:** Administradores visualizam apenas métricas agregadas; dados privados só mediante mecanismo auditado.
- **Auditoria:** Operações sensíveis gravam registro em `audit_logs` sem expor credenciais ou conteúdo sensível desnecessário.

---

## 7. Plano de Execução Incremental

- **Fase 1 — Fundação SaaS (Atual):** Estrutura do projeto, banco de dados completo (modelo base), autenticação e isolamento multiusuário, interface principal responsiva (14 seções + onboarding 6 etapas), importação e validação de currículo PDF/DOCX, cargos-alvo, empresas preferidas (com importação CSV) e preferências profissionais + configuração dos agentes + testes automatizados.
- **Fase 2 — Inteligência de Oportunidades:** Conectores viáveis (Greenhouse, Lever, JSON-LD), Company Watch, normalização/deduplicação, Motor de Aderência 0–100 e Dashboard de oportunidades.
- **Fase 3 — Candidaturas Supervisionadas & CRM:** Otimização ATS de currículos, respostas verificadas, fila de aprovação humana, envio supervisionado/manual, CRM (Tabela, Kanban, Calendário).
- **Fase 4 — Comercialização:** Planos, quotas no backend, gateway de pagamento BR, painel administrativo e controle de custos.
- **Fase 5 — Inteligência Avançada:** OAuth Gmail/Outlook, Interview Coach (STAR), analytics de coorte e exportação CSV/XLSX/PDF.

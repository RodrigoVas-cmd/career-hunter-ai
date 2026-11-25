# Career Hunter AI

Central inteligente de recolocação profissional (SaaS multiusuário) para profissionais de analista a diretoria.

## Estrutura do Projeto

- `docs/ARCHITECTURE.md` — Arquitetura, módulos, integrações viáveis, stack e plano por fases
- `docs/PHASE1_REPORT.md` — Relatório de entrega da Fase 1, testes, pendências e riscos
- `backend/` — API FastAPI + SQLAlchemy 2.0 (SQLite local / PostgreSQL produção)
- `frontend/` — Aplicação Web Next.js (App Router) + TypeScript + Tailwind CSS

## Como Executar Localmente

### 1. Backend (FastAPI)

```powershell
cd "c:\PROJETOS ANTIGRAVITY\carrier-hunter-ai\backend"
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

- Documentação interativa da API: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`

### 2. Frontend (Next.js)

```powershell
cd "c:\PROJETOS ANTIGRAVITY\carrier-hunter-ai\frontend"
npm.cmd run dev
```

- Aplicação web: `http://localhost:3000`

### 3. Testes Automatizados (Backend)

```powershell
cd "c:\PROJETOS ANTIGRAVITY\carrier-hunter-ai\backend"
.\.venv\Scripts\python.exe -m pytest -v
```

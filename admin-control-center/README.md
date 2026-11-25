# Career Hunter AI — Admin Control Center

Aplicação administrativa independente do Career Hunter AI.

## Estrutura Isolada
- `admin-control-center/backend/`: API FastAPI independente (porta padrão `8001`), tabelas próprias `admin_*` e RBAC no servidor (`superadmin`, `ops_admin`, `support`, `finance`).
- `admin-control-center/frontend/`: Interface Next.js App Router independente (porta padrão `3001`).

## Bootstrap do Primeiro Superadministrador
1. Suba o backend administrativo:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8001
   ```
2. Em produção, defina `ADMIN_BOOTSTRAP_TOKEN` e `ADMIN_JWT_SECRET_KEY`.
3. Acesse `/login` no frontend administrativo (porta `3001`) para criar o primeiro `superadmin` (operação permitida apenas uma única vez quando não há nenhum superadmin cadastrado).

## Testes e Build Independentes
- Backend: `pytest -v` (dentro de `admin-control-center/backend`)
- Frontend: `npx next build --webpack` (dentro de `admin-control-center/frontend`)

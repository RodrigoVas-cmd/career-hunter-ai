# Deploy em Produção — Supabase Cloud + Render + Vercel

Guia rápido para colocar o **Career Hunter AI** (Fases 1, 2 e 3) no ar usando a mesma arquitetura em nuvem do projeto Personal Trainer (**Supabase** para o banco PostgreSQL e **Vercel** para o frontend Next.js), com o backend FastAPI no **Render**.

---

## Etapa 1 — Banco de Dados no Supabase Cloud

1. Acesse [supabase.com](https://supabase.com) e crie um novo projeto (ex.: `career-hunter-ai`, região `South America (São Paulo)`).
2. No menu **Project Settings → Database** (ou botão **Connect** no topo):
   - Copie a URI do **Session pooler** (porta `5432`, compatível com IPv4):
     ```text
     postgresql://postgres.[PROJECT-REF]:[SUA-SENHA]@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
     ```
3. As tabelas serão criadas automaticamente na primeira inicialização da API (`Base.metadata.create_all`).

---

## Etapa 2 — Backend (FastAPI) no Render

1. Suba o repositório no GitHub.
2. No [render.com](https://render.com), clique em **New → Web Service** e selecione o repositório.
3. Configure:
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3` (ou `Docker` usando `backend/Dockerfile`)
   - **Build Command** *(se Python 3)*: `pip install -r requirements.txt`
   - **Start Command** *(se Python 3)*: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Em **Environment Variables**, adicione:
   - `ENVIRONMENT`: `production`
   - `DATABASE_URL`: *(URI do Supabase copiada na Etapa 1)*
   - `JWT_SECRET_KEY`: *(gere uma string aleatória longa, ex. 48+ caracteres)*
   - `CORS_ORIGINS`: `https://SEU-APP.vercel.app` *(atualize assim que tiver a URL da Vercel)*
   - `UPLOAD_DIR`: `/var/data/uploads` *(opcional: anexe um Persistent Disk em `/var/data` se quiser manter PDFs/DOCXs entre deploys)*
5. Após o deploy, teste `https://SUA-API.onrender.com/health` — deve retornar `{"status":"ok",...}`.

---

## Etapa 3 — Frontend (Next.js) na Vercel

1. No [vercel.com](https://vercel.com), clique em **Add New → Project** e importe o mesmo repositório.
2. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Next.js`
   - **Build Command**: `npx next build --webpack`
3. Em **Environment Variables**, adicione:
   - `NEXT_PUBLIC_API_URL`: `https://SUA-API.onrender.com/api/v1`
4. Faça o **Deploy**, copie a URL gerada pela Vercel (ex.: `https://career-hunter-ai.vercel.app`) e atualize `CORS_ORIGINS` no Render.
